
# app/main.py
from langchain_core.messages import HumanMessage
from fastapi import FastAPI, Header, Depends
from pydantic import BaseModel
from typing import Optional
from app.graph.graph import build_graph
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.services.farm_context_service import get_farm_context
from app.services.api_service import get_api_service
import time
from app.memory.redis_manager import redis_manager
from app.utils.timer import Timer
from app.config import llm
from datetime import datetime
import asyncio
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("cropeye-chatbot")

app = FastAPI(title="CropEye Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[int] = None  
    plot_id: Optional[str] = None


class InitializePlotRequest(BaseModel):
    plot_id: str  


class GenerateReportRequest(BaseModel):
    plot_id: str
    user_id: Optional[int] = None
    language: Optional[str] = None 


@app.on_event("startup")
async def preload_public_plots():
    print("\n🚀 Preloading public plots into cache...\n")

    api = get_api_service(None)

    try:
        data = await api.get_public_plots()

        if "error" not in data:
            redis_manager.set("public_plots", data, ttl=86400)
            print("✅ Public plots cached successfully")
        else:
            print("❌ Failed to preload plots:", data)

    except Exception as e:
        print("❌ Startup preload failed:", str(e))
        

async def call_with_retry(name, task, retries=3):
    for i in range(retries):
        try:
            result = await asyncio.wait_for(task(), timeout=15)
            return name, result
        except Exception as e:
            if i == retries - 1:
                return name, {"error": str(e)}
            await asyncio.sleep(2)


async def run_initialization(plot_id, token):
    api = get_api_service(token)
    try:
        plots = await api.get_public_plots()
        lat, lon = None, None

        for plot in plots.get("results", []):
            pid = plot.get("fastapi_plot_id")

            if str(pid) == str(plot_id):
                loc = plot.get("location", {})
                lat = loc.get("latitude")
                lon = loc.get("longitude")
                break

        if lat is None or lon is None:
            redis_manager.set_plot_status(plot_id, "failed")
            return
       
        today = datetime.now().strftime("%Y-%m-%d")

        tasks = {
        # ---------- SOIL ANALYSIS AGENT ----------
        "soil_analysis": lambda: api.get_soil_analysis(plot_id, today),
        "npk_requirements": lambda: api.get_npk_requirements(plot_id, today),

        # ---------- PEST ----------
        "pest_detection": lambda: api.get_pest_detection(plot_id, today),

        # ---------- IRRIGATION ----------
        "et": lambda: api.get_evapotranspiration(plot_id),
        "soil_moisture_timeseries": lambda: api.get_soil_moisture_timeseries(plot_id),

        # ---------- WEATHER ----------
        "current_weather": lambda: api.get_current_weather(plot_id, lat, lon),
        "weather_forecast": lambda: api.get_weather_forecast(plot_id, lat, lon),

        # ---------- MAPS ----------
        "growth_map": lambda: api.get_growth_map(plot_id, today),
        "soil_moisture_map": lambda: api.get_soil_moisture_map(plot_id, today),
        "water_uptake_map": lambda: api.get_water_uptake_map(plot_id, today),
        "pest_map": lambda: api.get_pest_map(plot_id, today),

        # ---------- DASHBOARD ----------
        "agro": lambda: api.get_agro_stats(plot_id, today),
        "harvest": lambda: api.get_harvest_status(plot_id),
        "stress":  lambda: api.get_stress_events(plot_id),
        "indices": lambda: api.get_field_indices(plot_id),
    }

        coroutines = [
            call_with_retry(name, task)
            for name, task in tasks.items()
        ]

        for coro in asyncio.as_completed(coroutines):
            await coro

        farm_context = await get_farm_context(
            plot_name=plot_id,
            user_id=None,
            auth_token=None
        )
        redis_manager.set_farm_context(plot_id, farm_context)
        print(f"\n🎉 ALL API DATA FETCHED FOR PLOT {plot_id} AT {datetime.now().strftime('%H:%M:%S')}\n")
        redis_manager.set_plot_status(plot_id, "ready")

    except Exception as e:
        logger.exception("Initialization failed")
        redis_manager.set_plot_status(plot_id, "failed")


@app.get("/")
def root():
    return {
        "message": "CropEye Chatbot API is running",
        "version": "1.0.0"
    }

@app.get("/health/redis")
def redis_health():
    try:
        redis_manager.client.ping()
        return {"status": "ok", "redis": "connected"}
    except:
        return {"status": "fail", "redis": "down"}


@app.post("/initialize-plot")
async def initialize_plot(request: InitializePlotRequest):
    plot_id = request.plot_id
    redis_manager.set_plot_status(plot_id, "processing")

    await run_initialization(plot_id, None)

    return {
        "status": "initializing",
        "message": "All APIs are being fetched in background"
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    auth_token = None
    timer = Timer()

    user_id = request.user_id 
    plot_id = request.plot_id 
    plot_id = str(plot_id)

    message_lower = request.message.lower().strip()
    simple_greetings = {
        "hi", "hello", "hey", "namaste", "नमस्ते", "thanks", "thank you", "bye", 
        "goodbye", "ok", "okay", "yes", "no", "hmm", "help", "who are you", "how are you", "how are you doing"
    }
    is_simple_greeting = message_lower in simple_greetings or (
        len(message_lower.split()) <= 2 and any(word in message_lower for word in ["hi", "hello", "hey", "thanks", "bye", "how are you", "how are you doing"])
    )

    thread_id = f"{user_id}_{plot_id}"
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    snapshot = graph.get_state(config)
    previous_values = snapshot.values if snapshot else {}
    
   
    
    if previous_values:
       
        conv_state = previous_values.get('conversation_state')
        
        if previous_values.get("messages"):
            for i, msg in enumerate(previous_values["messages"][-6:], 1):
                role = "Farmer" if msg.__class__.__name__ == "HumanMessage" else "Assistant"
                content_preview = msg.content[:150] + "..." if len(msg.content) > 150 else msg.content
                print(f"   {i}. {role}: {content_preview}")
    else:
        print("⚠️  No previous state - this is the FIRST message in conversation")
    print("="*80 + "\n")
 
    if previous_values.get("messages"):
        messages = previous_values["messages"]
    else:
        messages = []

    messages.append(HumanMessage(content=request.message))

    previous_intent = previous_values.get("intent")
    previous_entities = previous_values.get("entities", {})
    previous_conversation_state = previous_values.get("conversation_state")
    previous_language = previous_values.get("user_language")

    state = {
        "messages": messages,
        "user_language": previous_language, 
        "intent": None, 
        "entities": {},
        "conversation_state": previous_conversation_state, 
        "context": {
            "plot_id": request.plot_id,
            "user_id": request.user_id,
            "auth_token": auth_token,
        },
        "analysis": None,
        "final_response": None
    }

    farm_context = redis_manager.get_farm_context(plot_id)
    timer.step("farm context fetch")
    if not farm_context:
        return {"error": "Farm context not initialized. Please run /initialize-plot first."}

    state["context"].update(farm_context)

    logger.info(f"PLOT DEBUG → plot_id={state['context'].get('plot_id')} "
                f"lat={state['context'].get('lat')} "
                f"lon={state['context'].get('lon')}")

    if state["context"].get("lat") is None:
        return {"error": "Plot location missing"}
      
    status = redis_manager.get_plot_status(plot_id)
    timer.step("plot status fetch")
    if status != "ready":
        return {
                "status": status,
                "message": "Plot data still loading. Please wait..."
        }
    
    cached = redis_manager.get_plot_cached_data(plot_id)
    timer.step("redis sections fetch")
    state["context"]["cached_data"] = cached

    thread_id = f"{user_id}_{plot_id}"
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    result = await graph.ainvoke(state, config)
    timer.step("langgraph execution")
    
    response_preview = result.get('final_response', '')[:200] + "..." if len(result.get('final_response', '')) > 200 else result.get

    timer.total()
    
    return {
        "language": result.get("user_language"),
        "intent": result.get("intent"),
        "entities": result.get("entities"),
        "context": result.get("context"),
        "analysis": result.get("analysis"),
        "response": result.get("final_response")
    }


@app.post("/refresh-plot")
async def refresh_plot(request: InitializePlotRequest):
    return await initialize_plot(request)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Service is running"
    }


# if __name__ == "__main__":
#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)

@app.get("/debug/clear-cache")
async def clear_cache():
    redis_manager.client.flushdb()
    return {"status": "cache cleared"}
