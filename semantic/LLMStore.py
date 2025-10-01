from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI

from config import settings

class LLMStore:
  def __init__(self, provider: str | None = None) -> None:
    self.provider = provider or settings.EMBEDDER_NAME

  def get_llm(self):
    if self.provider == "ollama":
      return ChatOllama(
            model=settings.OLLAMA_MODEL,
            reasoning=False
        )

    if self.provider == "gemini":
      return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY
      )

    raise ValueError(
      f"Unsupported embedding provider '{self.provider}'. "
      "Expected one of: ['ollama', 'gemini']."
    )