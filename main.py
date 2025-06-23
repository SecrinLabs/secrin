import os
import time
from tqdm import tqdm
from packages.ai.embeddings.factory import get_embedder
from packages.ai.retriever.factory import get_vectorstore

MARKDOWN_BASE_DIR = "./data/cal-com"

def process_markdown_files(embedder, vectorstore):
    # Get list of all markdown files
    markdown_files = [f for f in os.listdir(MARKDOWN_BASE_DIR) if f.endswith(".md")]
    
    for filename in tqdm(markdown_files, desc="Processing markdown files"):
        try:
            filepath = os.path.join(MARKDOWN_BASE_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    continue

                doc_id = filename.replace(".md", "")
                if vectorstore.document_exists(doc_id):
                    print(f"⚠️ Document {doc_id} already exists, skipping...")
                    continue

                embedding = embedder.embed(content)
                vectorstore.add_document(
                    doc_id=doc_id,
                    embedding=embedding,
                    document=content,
                    metadata={"filename": filename}
                )

        except Exception as e:
            print(f"❌ Error processing file {filename}: {str(e)}")

def query_rag_system(question, embedder, vectorstore, n_results=3):
    query_embedding = embedder.embed(question)[0]
    documents = vectorstore.query(query_embedding, n_results=n_results)

    context = "\n".join(documents)
    prompt = f"""Based on the following documentation, please answer the question. 
If the answer cannot be found in the documentation, say so.

Documentation:
{context}

Question: {question}

Answer:"""

    from ollama import generate
    return generate(model="llama3.2", prompt=prompt)["response"]

def create_chatbot(embedder, vectorstore):
    print("\n🤖 Welcome to the Documentation Assistant!")
    print("Ask any question about the documentation (type 'exit' to quit)")
    
    while True:
        try:
            print("\n👤 You:", end=" ")
            question = input().strip()
            if question.lower() in ['exit', 'quit', 'bye']:
                print("\n🤖 Goodbye! Have a great day!")
                break
            if not question:
                print("Please ask a question!")
                continue

            print("🤖 Thinking", end="")
            for _ in range(3):
                time.sleep(0.3)
                print(".", end="", flush=True)
            print("\n")

            answer = query_rag_system(question, embedder, vectorstore)
            print("\n🤖 Assistant:", answer)
            print("\n" + "-"*50)

        except KeyboardInterrupt:
            print("\n\n🤖 Goodbye! Have a great day!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    embedder = get_embedder("ollama")
    vectorstore = get_vectorstore("chroma", collection_name="docs")

    process_markdown_files(embedder, vectorstore)
    create_chatbot(embedder, vectorstore)
