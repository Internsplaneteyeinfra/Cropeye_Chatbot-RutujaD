from fastapi import FastAPI, Header
from pydantic import BaseModel
from typing import Optional
from app.graph.graph import build_graph

app = FastAPI(title="CropEye Chatbot API")

graph = build_graph()


class ChatRequest(BaseModel):
    message: str
    user_id: Optional[int] = None
    plot_id: Optional[str] = None


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
    # Extract auth token from header
    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.replace("Bearer ", "")
    
    # Initialize state
    state = {
        "user_message": request.message,
        "user_language": None,
        "intent": None,
        "entities": {},
        "context": None,
        "analysis": None,
        "user_id": request.user_id,
        "auth_token": auth_token,
        "final_response": None
    }
    
    # If plot_id provided, add to entities
    if request.plot_id:
        if "entities" not in state:
            state["entities"] = {}
        state["entities"]["plot_id"] = request.plot_id

    # Run graph (async)
    result = await graph.ainvoke(state)
    print("FINAL GRAPH STATE", result)

    return {
        "language": result.get("user_language"),
        "intent": result.get("intent"),
        "entities": result.get("entities"),
        "context": result.get("context"),
        "analysis": result.get("analysis"),
        "response": result.get("final_response")
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Service is running"
    }
