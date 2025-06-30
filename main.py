import time
from tqdm import tqdm
from sqlalchemy.orm import Session
from packages.ai.embeddings.factory import get_embedder
from packages.ai.retriever.factory import get_vectorstore
from packages.scraper.src.models import engine
from packages.scraper.src.models.sitemap import Sitemap
from packages.scraper.src.models.githubissue import Issue
from packages.scraper.src.models.gitcommit import GitCommit
from ollama import generate

def safe_embed(embedder, text):
    try:
        embedding = embedder.embed(text)
        # Some embedders return [vector], some return vector
        if isinstance(embedding, list) and len(embedding) == 1 and isinstance(embedding[0], (list, tuple)):
            return embedding[0]
        return embedding
    except Exception as e:
        print(f"❌ Embedding error: {str(e)}")
        return None

def safe_query(vectorstore, query_embedding, n_results=3):
    try:
        results = vectorstore.query(query_embedding, n_results=n_results)
        # If the retriever returns a dict or object, extract text
        if isinstance(results, dict) and 'documents' in results:
            return results['documents']
        if isinstance(results, list):
            return results
        return []
    except Exception as e:
        print(f"❌ Vectorstore query error: {str(e)}")
        return []

def process_database_documents(embedder, vectorstore):
    # Create a database session
    session = Session(engine)
    
    # Get documents from sitemap
    sitemap_docs = session.query(Sitemap).all()

    for doc in tqdm(sitemap_docs, desc="Processing documentation"):
        try:
            doc_id = f"doc_{doc.id}"
            if vectorstore.document_exists(doc_id):
                # Document already exists, skipping...
                continue

            content = doc.markdown
            if not content:
                continue

            embedding = safe_embed(embedder, content)
            if embedding is None:
                continue
            vectorstore.add_document(
                doc_id=doc_id,
                embedding=embedding,
                document=content,
                metadata={"type": "documentation", "url": doc.url, "site": doc.site}
            )
        except Exception as e:
            print(f"❌ Error processing doc {doc.id}: {str(e)}")

    # Get issues and their related pull requests
    issues = session.query(Issue).all()
    for issue in tqdm(issues, desc="Processing issues"):
        try:
            doc_id = f"issue_{issue.id}"
            if vectorstore.document_exists(doc_id):
                # Issue already exists, skipping...
                continue

            # Combine issue and PR content
            content = f"Issue: {issue.title}\n\n{issue.body or ''}"
            if issue.pull_request:
                content += f"\n\nPull Request: {issue.pull_request.title}\n\n{issue.pull_request.body or ''}"
            
            if not content.strip():
                continue

            print(content)

            embedding = safe_embed(embedder, content)
            if embedding is None:
                continue
            vectorstore.add_document(
                doc_id=doc_id,
                embedding=embedding,
                document=content,
                metadata={
                    "type": "issue",
                    "url": issue.url,
                    "pr_url": issue.pull_request.url if issue.pull_request else None
                }
            )
        except Exception as e:
            print(f"❌ Error processing issue {issue.id}: {str(e)}")

        # Get commits from git_commits table
    commits = session.query(GitCommit).all()
    for commit in tqdm(commits, desc="Processing git commits"):
        try:
            doc_id = f"git_{commit.id}"
            if vectorstore.document_exists(doc_id):
                continue

            content = f"""Commit Message: {commit.message}
                Author: {commit.author}
                Date: {commit.date}
                Files Changed: {', '.join(commit.files)}
                Diff:
                {commit.diff}"""

            if not content.strip():
                continue

            embedding = safe_embed(embedder, content)
            if embedding is None:
                continue

            vectorstore.add_document(
                doc_id=doc_id,
                embedding=embedding,
                document=content,
                metadata={
                    "type": "commit",
                    "repo": commit.repo_name,
                    "hash": commit.commit_hash,
                    "author": commit.author,
                    "date": str(commit.date)
                }
            )
        except Exception as e:
            print(f"❌ Error processing commit {commit.id}: {str(e)}")

            
    session.close()

def query_rag_system(question, embedder, vectorstore, n_results=3):
    query_embedding = safe_embed(embedder, question)
    if query_embedding is None:
        return "❌ Could not generate embedding for your question."
    documents = safe_query(vectorstore, query_embedding, n_results=n_results)
    if not documents:
        return "The available sources do not contain the answer."
    context = "\n".join(documents)
    prompt = f"""You are a **technical analyst AI** assisting with software understanding. Your role is to answer the following question using **only** the provided information from:

            - 📄 Documentation
            - 🐛 GitHub Issues & Pull Requests

            Do **not** use any external knowledge or assumptions. Rely strictly on the content in the provided context.

            ---

            ### 📌 Instructions:
            1. Read the `Context` section carefully. It contains relevant documentation, issues, and pull request summaries.
            2. Analyze the `Question`.
            3. Construct an answer using **only** the information found in the context.
            4. If the question cannot be answered based on the context, respond with:
            > **"The available sources do not contain the answer."**
            5. Optionally, mention where the answer was derived from:
            - *(Based on Documentation)*  
            - *(Found in GitHub Issue)*  
            - *(Derived from Pull Request)*
            6. At the end, include a **confidence score** from 1 (low) to 5 (high), based on the answer's clarity and evidence from the sources.

            ---

            ### 🧠 Format:

            **Answer:** <your detailed answer>  
            **Source:** <source type if available>  
            **Confidence:** <1–5>

            ---

            ### 📚 Context (Documentation, Issues, PRs):
            {context}

            ---

            ### ❓ Question:
            {question}

            ---

            ### ✅ Final Answer:
            """

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

    process_database_documents(embedder, vectorstore)
    create_chatbot(embedder, vectorstore)
