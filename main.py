import ollama
import chromadb
import os
from tqdm import tqdm

MARKDOWN_BASE_DIR = "./data/cal-com"

def process_markdown_files():
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path="chroma_store")

    # Check if the collection exists
    existing_collections = client.list_collections()
    collection_name = "docs"

    print(existing_collections)

    if any(col.name == collection_name for col in existing_collections):
        print("Collection already exists. Updating documents...")
        collection = client.get_collection(name=collection_name)
    else:
        print("Creating new collection...")
        collection = client.create_collection(name=collection_name)

    # Get list of all markdown files
    markdown_files = [f for f in os.listdir(MARKDOWN_BASE_DIR) if f.endswith(".md")]
    
    # Process each file individually
    for filename in tqdm(markdown_files, desc="Processing markdown files"):
        try:
            filepath = os.path.join(MARKDOWN_BASE_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    continue

                # Generate document ID from filename
                doc_id = filename.replace(".md", "")

                # Check if document already exists in collection
                result = collection.get(ids=[doc_id])
                if result["ids"]:
                    print(f"⚠️ Document {doc_id} already exists, skipping...")
                    continue

                # Generate embedding for the document
                response = ollama.embed(model="mxbai-embed-large", input=content)
                embeddings = response["embeddings"]

                # Add document to collection
                collection.add(
                    ids=[doc_id],
                    embeddings=embeddings,
                    documents=[content],
                    metadatas=[{"filename": filename}]
                )

        except Exception as e:
            print(f"Error processing file {filename}: {str(e)}")

    return collection

def query_documents(query: str, collection, n_results: int = 5):
    """
    Query the document collection using semantic search
    """
    # Generate embedding for the query
    query_embedding = ollama.embed(model="mxbai-embed-large", input=query)["embeddings"]
    
    # Search for similar documents
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )
    
    return results

if __name__ == "__main__":
    # Process markdown files and get collection
    collection = process_markdown_files()

    # Test questions and expected keywords
    tests = [
      {
        "question": "explain me about booking-redirects...",
        "expected_keywords": [""]
      }
    ]

    # Function to run RAG query
    def query_rag_system(question):
        response = ollama.embed(model="mxbai-embed-large", input=question)
        embedded = response["embeddings"]
        results = collection.query(query_embeddings=embedded, n_results=3)
        context = "\n".join([doc for sublist in results["documents"] for doc in sublist])
        prompt = f"Using this data: {context}. Respond to this prompt: {question}"
        output = ollama.generate(model="llama3.2", prompt=prompt)
        return output["response"]

    # Evaluation loop
    for test in tests:
        answer = query_rag_system(test["question"])
        print(f"\nQ: {test['question']}\nA: {answer.strip()}")
        matched = [kw for kw in test["expected_keywords"] if kw.lower() in answer.lower()]
        print(f"Matched Keywords: {matched} / {len(test['expected_keywords'])}")

