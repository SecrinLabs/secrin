import time
from tqdm import tqdm
from sqlalchemy.orm import Session
from packages.ai.embeddings.factory import get_embedder
from packages.ai.retriever.factory import get_vectorstore
from packages.models import engine
from packages.models.sitemap import Sitemap
from packages.models.githubissue import Issue
from packages.models.gitcommit import GitCommit
from packages.models.integrations import Integration
from packages.config import get_config
from ollama import generate

config = get_config()

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
    
    # Get connected integrations
    connected_integrations = session.query(Integration).filter(Integration.is_connected == True).all()
    connected_integration_names = [integration.name for integration in connected_integrations]
    
    print(f"🔗 Connected integrations: {connected_integration_names}")
    
    if not connected_integration_names:
        print("❌ No connected integrations found. Skipping embedding process.")
        session.close()
        return
    
    # Process sitemap documents only if 'sitemap' integration is connected
    if 'sitemap' in connected_integration_names:
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
    else:
        print("⏭️ Skipping sitemap documents - integration not connected")

    # Process GitHub issues only if 'github' integration is connected
    if 'github' in connected_integration_names:
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
    else:
        print("⏭️ Skipping GitHub issues - integration not connected")

    # Process git commits only if 'gitlocal' or 'github' integration is connected
    if 'gitlocal' in connected_integration_names or 'github' in connected_integration_names:
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
    else:
        print("⏭️ Skipping git commits - neither gitlocal nor github integration connected")

            
    session.close()

def query_rag_system(question, embedder, vectorstore, n_results=3):
    query_embedding = safe_embed(embedder, question)
    if query_embedding is None:
        return "❌ Could not generate embedding for your question."
    documents = safe_query(vectorstore, query_embedding, n_results=n_results)
    if not documents:
        return "The available sources do not contain the answer."
    context = "\n".join(documents)
    prompt = f"""## 🧠 Developer Context Engine Prompt v1.1

            > You are a **Developer Context Engine AI**, helping engineers quickly understand the reasoning behind past changes related to a new software ticket.
            > Your role is to extract and summarize relevant information from the provided internal sources **only**.

            ---

            ### 🔒 Constraints

            * Use **only** the content in the `Context` section.
            * **Do not** make assumptions or use external knowledge.
            * **Do not** hallucinate information.

            ---

            ### 🧠 Your Thought Process

            1. Identify relevant components, modules, or features mentioned in the ticket.
            2. Locate any related:

            * 📄 **Documentation** — feature design, usage, known limitations
            * 🐛 **GitHub Issues & PRs** — problem discussions, decisions, reasons
            * 🔨 **Commits** — historical implementation details
            3. Determine whether the ticket relates to:

            * A regression, enhancement, refactor, or bugfix
            4. Use the evidence to infer **why previous decisions were made**, and how they affect the current ticket.

            ---

            ### 🔁 Output Format

            * ✅ **Answer**: Provide a clear and concise explanation.
            * 📎 **Source Tag** *(optional)*:

            * *(Found in PR #8493)*
            * *(Based on commit message from May 3)*
            * *(Derived from documentation on calendar logic)*

            If the question cannot be answered, respond with:

            > **"The available sources do not contain the answer."**

            ---

            ### 🗃️ Context (Docs, Issues, PRs, Commits):

            ```
            {context}
            ```

            ---

            ### ❓ Ticket Question:

            ```
            {question}
            ```

            ---

            ### ✅ Final Answer:
            """

    return generate(model=config.ollama_model, prompt=prompt)["response"]

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

def run_generator(question):
    embedder = get_embedder("ollama")
    vectorstore = get_vectorstore("chroma", collection_name=config.chroma_collection_name)
    answer = query_rag_system(question, embedder, vectorstore)
    return answer

def run_embedder():
    embedder = get_embedder("ollama")
    vectorstore = get_vectorstore("chroma", collection_name=config.chroma_collection_name)
    process_database_documents(embedder, vectorstore)