import base64
from fastapi import FastAPI, Header
from pydantic import BaseModel
from typing import Optional
from app.graph.graph import build_graph
from fastapi.middleware.cors import CORSMiddleware
from app.memory.redis_memory import get_memory, save_message
from app.services.voice_service import (
    transcribe_audio_base64,
    text_to_speech,
    get_tts_lang,
)


app = FastAPI(title="CropEye Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()

DEFAULT_PLOT_ID = "369_12"


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


@app.get("/")
def root():
    return {
        "message": "CropEye Chatbot API is running",
        "version": "1.0.0"
    }


@app.post("/chat")
async def chat(
    request: ChatRequest,
    authorization: Optional[str] = Header(None)
):
    # Extract auth token from header (same token as frontend after login)
    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.replace("Bearer ", "")
    

    user_id = request.user_id if request.user_id is not None else "default"
    plot_id = request.plot_id or DEFAULT_PLOT_ID
    plot_id = str(plot_id)
    # 🔹 Load Redis memory
    short_memory = get_memory(user_id, plot_id)

    # ---------- INITIAL GRAPH STATE ----------
    state = {
        "user_message": request.message,
        "user_language": None,
        "intent": None,
        "entities": {},
        "context": {
            "plot_id": request.plot_id or DEFAULT_PLOT_ID,
            "user_id": request.user_id,
            "auth_token": auth_token
        },
        "short_memory": short_memory,
        "analysis": None,
        "final_response": None
    }
   
    # Run graph (async)
    result = await graph.ainvoke(state)
    print("FINAL GRAPH STATE", result)

    # 🔹 Save Redis memory
    save_message(user_id, plot_id, "user", request.message)
    if result.get("final_response"):
        save_message(user_id, plot_id, "bot", result["final_response"])

    return {
        "language": result.get("user_language"),
        "intent": result.get("intent"),
        "entities": result.get("entities"),
        "context": result.get("context"),
        "analysis": result.get("analysis"),
        "response": result.get("final_response")
    }


# ---------- CropEye VoiceBot: same chatbot via voice (STT -> chat -> TTS) ----------
VOICE_ERROR_COULDNT_HEAR = "Sorry, I couldn't hear that. Please try again."
VOICE_ERROR_CHATBOT = "I'm having trouble right now. Please try again shortly."


@app.post("/voice/chat")
async def voice_chat(
    request: VoiceChatRequest,
    authorization: Optional[str] = Header(None),
):
    """
    CropEye VoiceBot: accept voice (audio) or text; pass to existing chatbot unchanged;
    return text response and optional TTS audio in the user's language.
    """
    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.replace("Bearer ", "")

    user_id = request.user_id if request.user_id is not None else "default"
    plot_id = request.plot_id or DEFAULT_PLOT_ID
    plot_id = str(plot_id)
    include_audio = request.include_audio is not False

    # Resolve user message: from text or from voice (STT)
    user_message = (request.message or "").strip()
    if not user_message and request.audio_base64:
        transcribed, _detected_lang = transcribe_audio_base64(
            request.audio_base64, request.content_type
        )
        print("🎤 RAW TRANSCRIBED TEXT:", transcribed)
        print("🌐 DETECTED LANGUAGE:", _detected_lang)
        
        user_message = (transcribed or "").strip()

    # Unclear or missing input
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

    # Run same chatbot logic as /chat (no modification of intent or response)
    short_memory = get_memory(user_id, plot_id)
    state = {
        "user_message": user_message,
        "user_language": None,
        "intent": None,
        "entities": {},
        "context": {
            "plot_id": request.plot_id or DEFAULT_PLOT_ID,
            "user_id": request.user_id,
            "auth_token": auth_token,
        },
        "short_memory": short_memory,
        "analysis": None,
        "final_response": None,
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

    save_message(user_id, plot_id, "user", user_message)
    if result.get("final_response"):
        save_message(user_id, plot_id, "bot", result["final_response"])

    # Use chatbot response as-is for TTS (no extra explanation or formatting)
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


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Service is running"
    }


# if __name__ == "__main__":
#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
