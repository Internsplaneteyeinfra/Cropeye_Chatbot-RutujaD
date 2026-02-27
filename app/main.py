# # app/main.py

# import base64
# from fastapi import FastAPI, Header, Depends
# from pydantic import BaseModel
# from typing import Optional
# from app.graph.graph import build_graph
# from fastapi.middleware.cors import CORSMiddleware
# import logging
# from app.services.farm_context_service import get_farm_context
# from app.services.api_service import get_api_service

# from app.memory.redis_manager import redis_manager

# from app.services.voice_service import (
#     transcribe_audio_base64,
#     text_to_speech,
#     get_tts_lang,
# )
# from datetime import datetime
# import asyncio

# # ---------------- LOGGING CONFIG ----------------
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
# )
# logger = logging.getLogger("cropeye-chatbot")
# # ------------------------------------------------

# app = FastAPI(title="CropEye Chatbot API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], 
#     allow_credentials=False,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# graph = build_graph()

# class ChatRequest(BaseModel):
#     message: str
#     user_id: Optional[int] = None  
#     plot_id: Optional[str] = None  


# class InitializePlotRequest(BaseModel):
#     plot_id: str


# class VoiceChatRequest(BaseModel):
#     """Voice input: send either typed message or voice audio. Response includes text + optional TTS audio."""
#     message: Optional[str] = None
#     audio_base64: Optional[str] = None
#     content_type: Optional[str] = None  # e.g. "audio/wav", "audio/mpeg"
#     user_id: Optional[int] = None
#     plot_id: Optional[str] = None
#     include_audio: Optional[bool] = True  # if True, return TTS as base64 


# @app.on_event("startup")
# async def preload_public_plots():
#     print("\n🚀 Preloading public plots into cache...\n")

#     api = get_api_service(None)

#     try:
#         data = await api.get_public_plots()

#         if "error" not in data:
#             redis_manager.set("public_plots", data, ttl=86400)
#             print("✅ Public plots cached successfully")
#         else:
#             print("❌ Failed to preload plots:", data)

#     except Exception as e:
#         print("❌ Startup preload failed:", str(e))
        

# async def run_initialization(plot_id, token):

#     api = get_api_service(token)

#     try:
#         plots = await api.get_public_plots()
#         lat, lon = None, None

#         for plot in plots.get("results", []):
#             pid = plot.get("fastapi_plot_id")

#             if str(pid) == str(plot_id):
#                 loc = plot.get("location", {})
#                 lat = loc.get("latitude")
#                 lon = loc.get("longitude")
#                 break

#         if lat is None or lon is None:
#             redis_manager.set_plot_status(plot_id, "failed")
#             return
       
#         today = datetime.now().strftime("%Y-%m-%d")

#         tasks = {
#         # ---------- SOIL ANALYSIS AGENT ----------
#         "soil_analysis": lambda: api.get_soil_analysis(plot_id, today),
#         "npk_requirements": lambda: api.get_npk_requirements(plot_id, today),

#         # ---------- PEST ----------
#         "pest_detection": lambda: api.get_pest_detection(plot_id, today),

#         # ---------- IRRIGATION ----------
#         "et": lambda: api.get_evapotranspiration(plot_id),
#         "soil_moisture_timeseries": lambda: api.get_soil_moisture_timeseries(plot_id),

#         # ---------- WEATHER ----------
#         "current_weather": lambda: api.get_current_weather(plot_id, lat, lon),
#         "weather_forecast": lambda: api.get_weather_forecast(plot_id, lat, lon),

#         # ---------- MAPS ----------
#         "growth_map": lambda: api.get_growth_map(plot_id, today),
#         "soil_moisture_map": lambda: api.get_soil_moisture_map(plot_id, today),
#         "water_uptake_map": lambda: api.get_water_uptake_map(plot_id, today),
#         "pest_map": lambda: api.get_pest_map(plot_id, today),

#         # ---------- DASHBOARD ----------
#         "agro": lambda: api.get_agro_stats(plot_id, today),
#         "harvest": lambda: api.get_harvest_status(plot_id),
#         "stress":  lambda: api.get_stress_events(plot_id),
#     }

#         results = {}

#         # -------------------------------
#         # RETRY LOGIC
#         # -------------------------------
#         for name, task in tasks.items():

#             for attempt in range(3):
#                 try:
#                     start = datetime.now()
#                     data = await task()

#                     if isinstance(data, dict) and data.get("error"):
#                         raise Exception(data["error"])

#                     results[name] = data
#                     break
                    
#                     end = datetime.now()
#                     duration = (end - start).total_seconds()

#                     print(f"✅ {name} completed in {duration:.2f}s at {end.strftime('%H:%M:%S')}")
#                     break

#                 except Exception as e:

#                     if attempt == 2:
#                         results[name] = {"error": str(e)}

#                     await asyncio.sleep(2)

#         redis_manager.set_plot(plot_id, results)
#         print(f"\n🎉 ALL API DATA FETCHED FOR PLOT {plot_id} AT {datetime.now().strftime('%H:%M:%S')}\n")
#         redis_manager.set_plot_status(plot_id, "ready")

#     except Exception as e:
#         logger.exception("Initialization failed")
#         redis_manager.set_plot_status(plot_id, "failed")


# @app.get("/")
# def root():
#     return {
#         "message": "CropEye Chatbot API is running",
#         "version": "1.0.0"
#     }

# @app.get("/health/redis")
# def redis_health():
#     try:
#         redis_manager.client.ping()
#         return {"status": "ok", "redis": "connected"}
#     except:
#         return {"status": "fail", "redis": "down"}


# @app.post("/initialize-plot")
# async def initialize_plot(request: InitializePlotRequest):
#     plot_id = request.plot_id
#     redis_manager.set_plot_status(plot_id, "processing")

#     asyncio.create_task(run_initialization(plot_id, None))

#     return {
#         "status": "initializing",
#         "message": "All APIs are being fetched in background"
#     }


# @app.post("/chat")

# async def chat(request: ChatRequest):
#     auth_token = None
    
#     user_id = request.user_id 
#     plot_id = request.plot_id 
#     plot_id = str(plot_id)

#     short_memory = redis_manager.get_memory(user_id, plot_id)

#     # ---------- INITIAL GRAPH STATE ----------
#     state = {
#         "user_message": request.message,
#         "user_language": None,
#         "intent": None,
#         "entities": {},
#         "context": {
#             "plot_id": request.plot_id,
#             "user_id": request.user_id,
#             "auth_token": auth_token
            
#         },
#         "short_memory": short_memory,
#         "analysis": None,
#         "final_response": None
#     }

#    # ---------- ENRICH CONTEXT WITH FARM DATA ----------
#     farm_context = await get_farm_context(
#         plot_name=state["context"]["plot_id"],
#         user_id=state["context"]["user_id"],
#         auth_token=state["context"]["auth_token"]
#     )

#     state["context"].update(farm_context)

#     logger.info(f"PLOT DEBUG → plot_id={state['context'].get('plot_id')} "
#             f"lat={state['context'].get('lat')} "
#             f"lon={state['context'].get('lon')}")


#     if state["context"].get("lat") is None:
#         return {"error": "Plot location missing"}

#     try:
#         status = redis_manager.get_plot_status(plot_id)

#         if status != "ready":
#             return {
#                 "status": status,
#                 "message": "Plot data still loading. Please wait..."
#             }

#         cached = redis_manager.get_plot(plot_id)
#     except:
#         cached = None

#     if not cached:
#         return {
#             "error": "Plot not initialized. Please call /initialize-plot first."
#         }
#     state["context"]["cached_data"] = cached

#     result = await graph.ainvoke(state)

#     redis_manager.save_message(user_id, plot_id, "user", request.message)
#     if result.get("final_response"):
#         redis_manager.save_message(user_id, plot_id, "bot", result["final_response"])

#     return {
#         "language": result.get("user_language"),
#         "intent": result.get("intent"),
#         "entities": result.get("entities"),
#         "context": result.get("context"),
#         "analysis": result.get("analysis"),
#         "response": result.get("final_response")
#     }


# # # ---------- CropEye VoiceBot: same chatbot via voice (STT -> chat -> TTS) ----------
# VOICE_ERROR_COULDNT_HEAR = "Sorry, I couldn't hear that. Please try again."
# VOICE_ERROR_CHATBOT = "I'm having trouble right now. Please try again shortly."


# @app.post("/voice/chat")

# async def voice_chat(request: VoiceChatRequest):
#     auth_token = None
#     """
#     CropEye VoiceBot: accept voice (audio) or text; pass to existing chatbot unchanged;
#     return text response and optional TTS audio in the user's language.
#     """

#     user_id = request.user_id 
#     plot_id = request.plot_id 
#     plot_id = str(plot_id)
#     include_audio = request.include_audio is not False

#     # Resolve user message: from text or from voice (STT)
#     user_message = (request.message or "").strip()
#     if not user_message and request.audio_base64:
#         transcribed, _detected_lang = transcribe_audio_base64(
#             request.audio_base64, request.content_type
#         )
#         print("🎤 RAW TRANSCRIBED TEXT:", transcribed)
#         print("🌐 DETECTED LANGUAGE:", _detected_lang)
        
#         user_message = (transcribed or "").strip()

#     # Unclear or missing input
#     if not user_message:
#         tts_lang = "en"
#         speak_text = VOICE_ERROR_COULDNT_HEAR
#         audio_base64_out = None
#         if include_audio:
#             audio_bytes = text_to_speech(speak_text, tts_lang)
#             audio_base64_out = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None
#         return {
#             "language": tts_lang,
#             "response": speak_text,
#             "speak_text": speak_text,
#             "audio_base64": audio_base64_out,
#             "transcribed": None,
#             "error": "voice_input_failed",
#         }

#     # Run same chatbot logic as /chat (no modification of intent or response)
#     short_memory = redis_manager.get_memory(user_id, plot_id)
#     state = {
#         "user_message": user_message,
#         "user_language": None,
#         "intent": None,
#         "entities": {},
#         "context": {
#             "plot_id": request.plot_id,
#             "user_id": request.user_id,
#             "auth_token": auth_token,
#         },
#         "short_memory": short_memory,
#         "analysis": None,
#         "final_response": None,
#     }

#     cached = redis_manager.get_plot(plot_id)
#     if not cached:
#         return {
#             "error": "Plot not initialized. Please call /initialize-plot first."
#         }
#     state["context"]["cached_data"] = cached

#     try:
#         result = await graph.ainvoke(state)
#     except Exception:
#         speak_text = VOICE_ERROR_CHATBOT
#         tts_lang = "en"
#         audio_base64_out = None
#         if include_audio:
#             audio_bytes = text_to_speech(speak_text, tts_lang)
#             audio_base64_out = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None
#         return {
#             "language": tts_lang,
#             "response": speak_text,
#             "speak_text": speak_text,
#             "audio_base64": audio_base64_out,
#             "transcribed": user_message,
#             "error": "chatbot_error",
#         }

#     # save_message(user_id, plot_id, "user", user_message)
#     redis_manager.save_message(user_id, plot_id, "user", user_message)
#     if result.get("final_response"):
#         redis_manager.save_message(user_id, plot_id, "bot", result["final_response"])

#     # Use chatbot response as-is for TTS (no extra explanation or formatting)
#     final_response = result.get("final_response") or ""
#     user_language = result.get("user_language")
#     tts_lang = get_tts_lang(user_language)
#     speak_text = final_response
#     audio_base64_out = None
#     if include_audio and speak_text:
#         audio_bytes = text_to_speech(speak_text, tts_lang)
#         audio_base64_out = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None

#     return {
#         "language": result.get("user_language"),
#         "intent": result.get("intent"),
#         "entities": result.get("entities"),
#         "context": result.get("context"),
#         "analysis": result.get("analysis"),
#         "response": final_response,
#         "speak_text": speak_text,
#         "audio_base64": audio_base64_out,
#         "transcribed": user_message if request.audio_base64 else None,
#         "error": None,
#     }

# @app.post("/refresh-plot")

# async def refresh_plot(plot_id:str):
#     return await initialize_plot(plot_id)

# @app.get("/health")
# def health_check():
#     return {
#         "status": "ok",
#         "message": "Service is running"
#     }


# # if __name__ == "__main__":
# #     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)

# @app.get("/debug/clear-cache")
# async def clear_cache():
#     redis_manager.client.flushdb()
#     return {"status": "cache cleared"}




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

from app.memory.redis_manager import redis_manager

from app.services.voice_service import (
    transcribe_audio_base64,
    text_to_speech,
    get_tts_lang,
)
from datetime import datetime
import asyncio

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


class VoiceChatRequest(BaseModel):
    """Voice input: send either typed message or voice audio. Response includes text + optional TTS audio."""
    message: Optional[str] = None
    audio_base64: Optional[str] = None
    content_type: Optional[str] = None  # e.g. "audio/wav", "audio/mpeg"
    user_id: Optional[int] = None
    plot_id: Optional[str] = None
    include_audio: Optional[bool] = True  # if True, return TTS as base64 


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
    }

        results = {}

        # -------------------------------
        # RETRY LOGIC
        # -------------------------------
        for name, task in tasks.items():

            for attempt in range(3):
                try:
                    start = datetime.now()
                    # data = await task
                    # results[name] = data
                    data = await task()

                    # treat API error response as failure
                    if isinstance(data, dict) and data.get("error"):
                        raise Exception(data["error"])

                    results[name] = data
                    break
                    
                    end = datetime.now()
                    duration = (end - start).total_seconds()

                    print(f"✅ {name} completed in {duration:.2f}s at {end.strftime('%H:%M:%S')}")
                    break
                except Exception as e:

                    if attempt == 2:
                        results[name] = {"error": str(e)}

                    await asyncio.sleep(2)

        redis_manager.set_plot(plot_id, results)
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
async def initialize_plot(plot_id: str):
    redis_manager.set_plot_status(plot_id, "processing")

    asyncio.create_task(run_initialization(plot_id, None))

    return {
        "status": "initializing",
        "message": "All APIs are being fetched in background"
    }


@app.post("/chat")
async def chat(request: ChatRequest):
    auth_token = None

    user_id = request.user_id 
    plot_id = request.plot_id 
    plot_id = str(plot_id)

    short_memory = redis_manager.get_memory(user_id, plot_id)

    # ---------- INITIAL GRAPH STATE ----------
    state = {
        "user_message": request.message,
        "user_language": None,
        "intent": None,
        "entities": {},
        "context": {
            "plot_id": request.plot_id,
            "user_id": request.user_id,
            "auth_token": auth_token
            
        },
        "short_memory": short_memory,
        "analysis": None,
        "final_response": None
    }

   # ---------- ENRICH CONTEXT WITH FARM DATA ----------
    farm_context = await get_farm_context(
        plot_name=state["context"]["plot_id"],
        user_id=state["context"]["user_id"],
        auth_token=state["context"]["auth_token"]
    )

    state["context"].update(farm_context)

    logger.info(f"PLOT DEBUG → plot_id={state['context'].get('plot_id')} "
            f"lat={state['context'].get('lat')} "
            f"lon={state['context'].get('lon')}")


    if state["context"].get("lat") is None:
        return {"error": "Plot location missing"}

    try:
        status = redis_manager.get_plot_status(plot_id)

        if status != "ready":
            return {
                "status": status,
                "message": "Plot data still loading. Please wait..."
            }

        cached = redis_manager.get_plot(plot_id)
    except:
        cached = None

    if not cached:
        return {
            "error": "Plot not initialized. Please call /initialize-plot first."
        }
    state["context"]["cached_data"] = cached

    result = await graph.ainvoke(state)

    redis_manager.save_message(user_id, plot_id, "user", request.message)
    if result.get("final_response"):
        redis_manager.save_message(user_id, plot_id, "bot", result["final_response"])

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
        print("🎤 RAW TRANSCRIBED TEXT:", transcribed)
        print("🌐 DETECTED LANGUAGE:", _detected_lang)
        
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

    cached = redis_manager.get_plot(plot_id)
    if not cached:
        return {
            "error": "Plot not initialized. Please call /initialize-plot first."
        }
    state["context"]["cached_data"] = cached

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
async def refresh_plot(plot_id:str):
    return await initialize_plot(plot_id)

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
