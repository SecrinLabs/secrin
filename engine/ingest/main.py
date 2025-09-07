import psycopg2
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from config import settings

async def update_vectorstore():
    conn = psycopg2.connect(settings.DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT id, repo_name, description FROM repositories WHERE description IS NOT NULL")
    rows = cur.fetchall()
    conn.close()

    docs = [
        Document(page_content=row[2], metadata={"id": row[0], "repo_name": row[1]})
        for row in rows
    ]

    if not docs:
        return None

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=settings.GEMINI_API_KEY,
    )

    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    vectorstore.persist()
    return vectorstore
