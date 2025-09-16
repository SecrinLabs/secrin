from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from engine.embeddings.base import BaseStore
from config import settings

class GeminiStore(BaseStore):
  def getEmbedder(self):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=settings.GEMINI_API_KEY,
    )
    return embeddings
  
  def getLlm(self):
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-lite",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.2,
    )
    return llm