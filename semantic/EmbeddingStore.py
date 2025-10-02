from langchain_ollama import OllamaEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config import settings

class EmbeddingStore:
    def __init__(self, provider: str | None = None) -> None:
        self.provider = provider or settings.EMBEDDER_NAME

    def get_embedding(self):
        if self.provider == "ollama":
            return OllamaEmbeddings(model="mxbai-embed-large")

        if self.provider == "gemini":
            return GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-001",
                google_api_key=settings.GEMINI_API_KEY
            )

        raise ValueError(
            f"Unsupported embedding provider '{self.provider}'. "
            "Expected one of: ['ollama', 'gemini']."
        )
