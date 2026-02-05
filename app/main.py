from fastapi import FastAPI, Header
from pydantic import BaseModel
from typing import Optional
from app.graph.graph import build_graph

app = FastAPI(title="CropEye Chatbot API")

graph = build_graph()

DEFAULT_PLOT_ID = "369_12"


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
    """
    Chat endpoint - processes user messages through the chatbot graph
    
    NOTE: For development without authentication:
    - authorization header is optional
    - user_id is optional
    - plot_id can be provided
    - Chatbot will work with plot-based APIs that don't require authentication
    """
    # Extract auth token from header (optional during development)
    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization.replace("Bearer ", "")
    
    
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
        "analysis": None,
        "final_response": None
    }
   
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


# if __name__ == "__main__":
#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
