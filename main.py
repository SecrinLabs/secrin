import ollama
import chromadb
import os
from tqdm import tqdm
import time

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

def create_chatbot(collection):
    print("\n🤖 Welcome to the Documentation Assistant!")
    print("Ask any question about the documentation (type 'exit' to quit)")
    
    while True:
        try:
            # Get user input
            print("\n👤 You:", end=" ")
            question = input().strip()
            
            # Check for exit command
            if question.lower() in ['exit', 'quit', 'bye']:
                print("\n🤖 Goodbye! Have a great day!")
                break
            
            if not question:
                print("Please ask a question!")
                continue
            
            # Show thinking animation
            print("🤖 Thinking", end="")
            for _ in range(3):
                time.sleep(0.3)
                print(".", end="", flush=True)
            print("\n")
            
            # Query the RAG system
            response = query_rag_system(question)
            
            # Print the response
            print("\n🤖 Assistant:", response)
            print("\n" + "-"*50)
            
        except KeyboardInterrupt:
            print("\n\n🤖 Goodbye! Have a great day!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try asking your question again.")

def query_rag_system(question):
    """
    Process a question through the RAG system
    """
    # Get embeddings for the question
    response = ollama.embed(model="mxbai-embed-large", input=question)
    embedded = response["embeddings"]
    
    # Query the collection for relevant documents
    results = collection.query(query_embeddings=embedded, n_results=3)
    
    # Combine the relevant documents
    context = "\n".join([doc for sublist in results["documents"] for doc in sublist])
    
    # Create a prompt with the context and question
    prompt = f"""Based on the following documentation, please answer the question. 
      If the answer cannot be found in the documentation, say so.

      Documentation:
      {context}

      Question: {question}

      Answer:"""
    
    # Generate response using LLM
    output = ollama.generate(model="llama3.2", prompt=prompt)
    return output["response"]

if __name__ == "__main__":
    # Process markdown files and get collection
    collection = process_markdown_files()
    
    # Start the interactive chatbot
    create_chatbot(collection)

