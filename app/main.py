
# app/main.py

import base64
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
from app.services.voice_service import (
    transcribe_audio_base64,
    text_to_speech,
    get_tts_lang,
)
from app.services.report_service import get_report_data
from app.prompts.response_prompt import YIELD_IMPROVEMENT_PROMPT
from app.config import llm
from app.utils.lang_detect import detect_lang
from datetime import datetime
import asyncio
import json
from app.services.farm_context_service import get_farm_context

# ---------------- LOGGING CONFIG ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("cropeye-chatbot")
# ------------------------------------------------

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


class VoiceChatRequest(BaseModel):
    """Voice input: send either typed message or voice audio. Response includes text + optional TTS audio."""
    message: Optional[str] = None
    audio_base64: Optional[str] = None
    content_type: Optional[str] = None  # e.g. "audio/wav", "audio/mpeg"
    user_id: Optional[int] = None
    plot_id: Optional[str] = None
    include_audio: Optional[bool] = True  # if True, return TTS as base64


class GenerateReportRequest(BaseModel):
    plot_id: str
    user_id: Optional[int] = None
    language: Optional[str] = None  # Optional language override (e.g., "en", "hi", "mr") 


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

        results = {}

        for coro in asyncio.as_completed(coroutines):
            name, result = await coro
            results[name] = result

        # redis_manager.set_plot(plot_id, results)
        for section, data in results.items():
            redis_manager.set_plot_section(plot_id, section, data)

        # ---------- PRECOMPUTE FARM CONTEXT ----------
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

    asyncio.create_task(run_initialization(plot_id, None))

    return {
        "status": "initializing",
        "message": "All APIs are being fetched in background"
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    auth_token = None
    # chat_start = time.perf_counter()
    timer = Timer()

    user_id = request.user_id 
    plot_id = request.plot_id 
    plot_id = str(plot_id)

    short_memory = redis_manager.get_memory(user_id, plot_id)
    timer.step("memory fetch")
    # ---------- FAST GREETING DETECTION (skip farm context for simple greetings) ----------
    message_lower = request.message.lower().strip()
    simple_greetings = {
        "hi", "hello", "hey", "namaste", "नमस्ते", "thanks", "thank you", "bye", 
        "goodbye", "ok", "okay", "yes", "no", "hmm", "help", "who are you", "how are you", "how are you doing"
    }
    is_simple_greeting = message_lower in simple_greetings or (
        len(message_lower.split()) <= 2 and any(word in message_lower for word in ["hi", "hello", "hey", "thanks", "bye", "how are you", "how are you doing"])
    )

    # ---------- INITIAL GRAPH STATE ----------
    state = {
        "user_message": request.message,
        "user_language": None,
        "intent": None,
        "entities": {},
        "context": {
            "plot_id": request.plot_id,
            "user_id": request.user_id,
            "auth_token": auth_token,
        },
        "short_memory": short_memory,
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
    cached = redis_manager.get_all_plot_sections(plot_id)
    timer.step("redis sections fetch")
    state["context"]["cached_data"] = cached

    result = await graph.ainvoke(state)
    timer.step("langgraph execution")

    redis_manager.save_message(user_id, plot_id, "user", request.message)
    timer.step("save user message")

    if result.get("final_response"):
        redis_manager.save_message(user_id, plot_id, "bot", result["final_response"])
        
    timer.step("save bot message")

    timer.total()
    # print(f"⏱ TOTAL CHAT TIME: {time.perf_counter() - chat_start:.3f}s")
    
    return {
        "language": result.get("user_language"),
        "intent": result.get("intent"),
        "entities": result.get("entities"),
        "context": result.get("context"),
        "analysis": result.get("analysis"),
        "response": result.get("final_response")
    }


# # ---------- CropEye VoiceBot: same chatbot via voice (STT -> chat -> TTS) ----------
VOICE_ERROR_COULDNT_HEAR = "Sorry, I couldn't hear that. Please try again."
VOICE_ERROR_CHATBOT = "I'm having trouble right now. Please try again shortly."


@app.post("/voice/chat")
async def voice_chat(request: VoiceChatRequest):
    auth_token = None
    """
    CropEye VoiceBot: accept voice (audio) or text; pass to existing chatbot unchanged;
    return text response and optional TTS audio in the user's language.
    """
    user_id = request.user_id 
    plot_id = request.plot_id 
    plot_id = str(plot_id)
    include_audio = request.include_audio is not False

    user_message = (request.message or "").strip()
    if not user_message and request.audio_base64:
        transcribed, _detected_lang = transcribe_audio_base64(
            request.audio_base64, request.content_type
        )
        # ---------- DISABLE VERBOSE LOGGING FOR PERFORMANCE ----------
        # print("🎤 RAW TRANSCRIBED TEXT:", transcribed)
        # print("🌐 DETECTED LANGUAGE:", _detected_lang)
        
        user_message = (transcribed or "").strip()

    if not user_message:
        tts_lang = "en"
        speak_text = VOICE_ERROR_COULDNT_HEAR
        audio_base64_out = None
        if include_audio:
            audio_bytes = text_to_speech(speak_text, tts_lang)
            audio_base64_out = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None
        return {
            "language": tts_lang,
            "response": speak_text,
            "speak_text": speak_text,
            "audio_base64": audio_base64_out,
            "transcribed": None,
            "error": "voice_input_failed",
        }

    short_memory = redis_manager.get_memory(user_id, plot_id)
    state = {
        "user_message": user_message,
        "user_language": None,
        "intent": None,
        "entities": {},
        "context": {
            "plot_id": request.plot_id,
            "user_id": request.user_id,
            "auth_token": auth_token,
        },
        "short_memory": short_memory,
        "analysis": None,
        "final_response": None,
    }
    # start = time.perf_counter()
    # cached = redis_manager.get_plot(plot_id)
    # print(f"⏱ plot cache fetch took {time.perf_counter()-start:.3f}s")

    # if not cached:
    #     return {
    #         "error": "Plot not initialized. Please call /initialize-plot first."
    #     }
    # state["context"]["cached_data"] = cached

    status = redis_manager.get_plot_status(plot_id)
    if status != "ready":
        return {
            "error": "Plot data still loading. Please wait..."
        }

    try:
        result = await graph.ainvoke(state)
    except Exception:
        speak_text = VOICE_ERROR_CHATBOT
        tts_lang = "en"
        audio_base64_out = None
        if include_audio:
            audio_bytes = text_to_speech(speak_text, tts_lang)
            audio_base64_out = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None
        return {
            "language": tts_lang,
            "response": speak_text,
            "speak_text": speak_text,
            "audio_base64": audio_base64_out,
            "transcribed": user_message,
            "error": "chatbot_error",
        }

    redis_manager.save_message(user_id, plot_id, "user", user_message)
    if result.get("final_response"):
        redis_manager.save_message(user_id, plot_id, "bot", result["final_response"])

    final_response = result.get("final_response") or ""
    user_language = result.get("user_language")
    tts_lang = get_tts_lang(user_language)
    speak_text = final_response
    audio_base64_out = None
    if include_audio and speak_text:
        audio_bytes = text_to_speech(speak_text, tts_lang)
        audio_base64_out = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None

    return {
        "language": result.get("user_language"),
        "intent": result.get("intent"),
        "entities": result.get("entities"),
        "context": result.get("context"),
        "analysis": result.get("analysis"),
        "response": final_response,
        "speak_text": speak_text,
        "audio_base64": audio_base64_out,
        "transcribed": user_message if request.audio_base64 else None,
        "error": None,
    }

@app.post("/refresh-plot")
async def refresh_plot(request: InitializePlotRequest):
    return await initialize_plot(request)

@app.post("/generate-report")
async def generate_report(request: GenerateReportRequest):
    """
    Generate a comprehensive yield improvement report for a plot.
    Uses cached farm data and domain logic to provide actionable recommendations.
    """
    plot_id = str(request.plot_id)
    user_id = request.user_id
    language = request.language
    
    start_time = time.perf_counter()
    
    # Step 1: Check if plot is initialized
    try:
        status = redis_manager.get_plot_status(plot_id)
        if status != "ready":
            return {
                "error": "Plot not ready",
                "status": status,
                "message": "Plot data still loading. Please wait..."
            }
    except Exception as e:
        logger.error(f"Error checking plot status: {e}")
        return {"error": "Failed to check plot status"}
    
    # Step 2: Fetch cached farm data and process through domain logic
    try:
        report_data = await get_report_data(
            plot_id=plot_id,
            user_id=user_id,
            auth_token=None
        )
        
        if report_data.get("error"):
            return {"error": report_data.get("error")}
            
    except Exception as e:
        logger.exception("Error fetching report data")
        return {"error": f"Failed to fetch report data: {str(e)}"}
    
    # Step 3: Detect language if not provided
    if not language:
        # Use a default message to detect language preference
        # In production, you might want to use user preferences or previous chat history
        language = "en"  # Default to English
    
    # Step 4: Summarize data for LLM (reduce token usage)
    # Extract key metrics only
    summary = {
        "farm_context": {
            "crop_stage": report_data.get("farm_context", {}).get("crop_stage"),
            "days_since_plantation": report_data.get("farm_context", {}).get("days_since_plantation"),
            "kc": report_data.get("farm_context", {}).get("kc"),
            "plantation_date": report_data.get("farm_context", {}).get("plantation_date"),
        },
        "yield": report_data.get("yield", {}),
        "biomass": report_data.get("biomass", {}),
        "crop_status": report_data.get("crop_status", {}),
        "soil": report_data.get("soil", {}),
        "npk_requirements": report_data.get("npk_requirements", {}),
        "irrigation": report_data.get("irrigation", {}),
        "pest_risk": report_data.get("pest_risk", {}),
        "weather": {
            "current": {
                "temperature_c": report_data.get("weather", {}).get("current", {}).get("temperature_c"),
                "humidity": report_data.get("weather", {}).get("current", {}).get("humidity"),
                "precip_mm": report_data.get("weather", {}).get("current", {}).get("precip_mm"),
            }
        },
        "indices": {
            "latest": report_data.get("indices", {}).get("series", [])[-1] if report_data.get("indices", {}).get("series") else {},
            "critical_events": report_data.get("indices", {}).get("critical_events", []),
        },
        "stress": report_data.get("stress", {}),
        "sugar_content": report_data.get("sugar_content", {}),
        "evapotranspiration": {
            "ET_mean_mm_per_day": report_data.get("evapotranspiration", {}).get("ET_mean_mm_per_day"),
        },
    }
    
    # Step 5: Generate report using LLM
    try:
        prompt = YIELD_IMPROVEMENT_PROMPT.format(
            language=language,
            context=json.dumps(report_data.get("farm_context", {}), indent=2),
            analysis=json.dumps(summary, indent=2),
            user_message="Generate a comprehensive yield improvement report to help reach 100T yield target."
        )
        
        logger.info(f"Generating yield improvement report for plot {plot_id}")
        llm_start = time.perf_counter()
        response = llm.invoke(prompt)
        logger.info(f"⏱ LLM call took {time.perf_counter() - llm_start:.3f}s")
        
        # Extract content from response
        if hasattr(response, 'content'):
            report_text = response.content
        elif hasattr(response, 'text'):
            report_text = response.text
        elif isinstance(response, str):
            report_text = response
        else:
            report_text = str(response)
        
        # Clean up the response
        report_text = report_text.strip()
        if report_text.startswith("```"):
            # Remove markdown code blocks if present
            lines = report_text.split("\n")
            report_text = "\n".join([l for l in lines if not l.strip().startswith("```")])
        
    except Exception as e:
        logger.exception("Error generating report with LLM")
        return {"error": f"Failed to generate report: {str(e)}"}
    
    total_time = time.perf_counter() - start_time
    logger.info(f"⏱ Total report generation time: {total_time:.3f}s")
    
    return {
        "plot_id": plot_id,
        "language": language,
        "report": report_text,
        "timestamp": datetime.now().isoformat(),
        "processing_time_seconds": round(total_time, 3)
    }


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
