# vector_db.py
import chromadb
import google.generativeai as genai
from chromadb.config import Settings
from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def gemini_embedding(texts):
    embeddings = []
    for text in texts:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text
        )
        embeddings.append(result["embedding"])
    return embeddings


# 🔹 ChromaDB setup (persistent)
client = chromadb.Client(
    Settings(
        persist_directory="./chroma_db",
        anonymized_telemetry=False
    )
)

collection = client.get_or_create_collection(
    name="irrigation_faq_embed",
    embedding_function=gemini_embedding
)


# 🔹 Add documents (run once)
def add_faqs(faq_list):
    collection.add(
        documents=faq_list,
        ids=[f"faq_{i}" for i in range(len(faq_list))]
    )
    print("✅ FAQs added to ChromaDB")


# 🔹 Search FAQ
def search_faq(question):
    result = collection.query(
        query_texts=[question],
        n_results=1
    )

    if not result["documents"]:
        return None

    return result["documents"][0][0]
