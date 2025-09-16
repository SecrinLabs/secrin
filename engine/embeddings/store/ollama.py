from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama

from config import settings
from engine.embeddings.base import BaseStore

class OllamaStore(BaseStore):
  def getEmbedder(self):
    embeddings = OllamaEmbeddings(
        model="mxbai-embed-large"
    )
    return embeddings
  
  def getLlm(self):
    llm = ChatOllama(model=settings.OLLAMA_MODEL or "deepseek-r1:1.5b")
    return llm