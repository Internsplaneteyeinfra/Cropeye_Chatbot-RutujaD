# from langchain_ollama import ChatOllama

from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
import warnings

load_dotenv()

# llm = ChatOllama(
#     model=os.getenv("OLLAMA_MODEL", "mistral"),
#     base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
#     temperature=float(os.getenv("OLLAMA_TEMPERATURE", 0))
# )

# Validate API key before initializing LLM
gemini_api_key = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    api_key=gemini_api_key,
    temperature=float(os.getenv("GEMINI_TEMPERATURE", 0))
)