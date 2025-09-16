from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from config import settings


class QueryRequest(BaseModel):
    question: str


# Choose embeddings dynamically
if settings.EMBEDDER_NAME == "gemini":
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=settings.GEMINI_API_KEY,
    )
elif settings.EMBEDDER_NAME == "ollama":
    embeddings = OllamaEmbeddings(
        model=settings.OLLAMA_MODEL or "mxbai-embed-large"  # default Ollama embedding model
    )
else:
    raise ValueError(f"Unsupported embedder: {settings.EMBEDDER_NAME}")


# Initialize vectorstore
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})


# Choose LLM dynamically (if you want to switch LLMs too)
if settings.EMBEDDER_NAME == "gemini":
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-lite",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.2,
    )
elif settings.EMBEDDER_NAME == "ollama":
    from langchain_community.chat_models import ChatOllama

    llm = ChatOllama(model=settings.OLLAMA_MODEL or "llama3")
else:
    raise ValueError(f"Unsupported LLM: {settings.LLM_NAME}")


# Prompt template
qa_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "You are an assistant. Use the context to answer the question.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer clearly and concisely:"
    ),
)

# RetrievalQA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff",
    chain_type_kwargs={"prompt": qa_prompt},
    return_source_documents=False,
)
