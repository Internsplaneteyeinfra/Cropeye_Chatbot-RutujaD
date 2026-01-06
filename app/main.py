from fastapi import FastAPI
from pydantic import BaseModel

from app.graph.graph import build_graph

app = FastAPI(title="CropEye Chatbot API")

graph = build_graph()


class ChatRequest(BaseModel):
    message: str

@app.get("/")
def root():
    return {
        "message": "CropEye Chatbot API is running"
    }

@app.post("/chat")
def chat(request: ChatRequest):
    state = {
        "user_message": request.message,
        "user_language": "",
        "intent": "",
        "entities": {},
        "final_response": ""
    }

    result = graph.invoke(state)
    print("FINAL GRAPH STATE", result)

    return {
        "language": result.get("user_language"),
        "intent": result.get("intent"),
        "entities": result.get("entities"),
        "response": result.get("final_response")
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Service is running"
    }

