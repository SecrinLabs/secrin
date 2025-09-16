from pydantic import BaseModel
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from engine.embeddings.factory import get_store

class QueryRequest(BaseModel):
    question: str

store = get_store()

# Get embeddings and LLM from store
embeddings = store.getEmbedder()
llm = store.getLlm()

# Initialize vectorstore
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

qa_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "You are a careful assistant. Your job is to answer strictly based on the provided context.\n\n"
        "### Rules:\n"
        "- Use ONLY the information in the Context section.\n"
        "- Do NOT use external knowledge or make assumptions.\n"
        "- If the answer is not present in the context, say: 'The context does not provide that information.'\n\n"
        "### Context:\n{context}\n\n"
        "### Question:\n{question}\n\n"
        "### Answer:"
    ),
)

# RetrievalQA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff",
    chain_type_kwargs={"prompt": qa_prompt},
    return_source_documents=True,
)
