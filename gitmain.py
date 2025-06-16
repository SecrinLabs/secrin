import ollama
import chromadb
from git import Repo

# Sample documents on human behavior
documents = [
  "Humans are inherently social creatures, often seeking connection and belonging in groups.",
  "The human brain is wired to recognize patterns, even when none exist — a behavior known as apophenia.",
  "People tend to conform to group norms, even if those norms contradict their personal beliefs or logic.",
  "Humans experience a cognitive bias called the 'confirmation bias' where they favor information that supports their existing views.",
  "Most people have a limited attention span, with studies suggesting focus drops significantly after 20 minutes.",
  "Empathy is a key part of human relationships, allowing people to emotionally connect and understand others’ feelings.",
  "Stress triggers a 'fight or flight' response, activating physiological changes such as increased heart rate and alertness.",
  "Dopamine, a neurotransmitter, plays a major role in motivation, pleasure, and reinforcement learning in human behavior.",
  "Humans often mirror the emotions and expressions of those around them, a phenomenon called emotional contagion.",
  "The fear of rejection can strongly influence human decision-making, often more than the desire for reward."
]

# Initialize ChromaDB client
client = chromadb.PersistentClient(path="chroma_store")

# Check if the collection exists
existing_collections = client.list_collections()
collection_name = "docs"

if any(col.name == collection_name for col in existing_collections):
    collection = client.get_collection(name=collection_name)
else:
    collection = client.create_collection(name=collection_name)
    for i, d in enumerate(documents):
        response = ollama.embed(model="mxbai-embed-large", input=d)
        embeddings = response["embeddings"]
        collection.add(
            ids=[str(i)],
            embeddings=embeddings,
            documents=[d]
        )

# Ingest Git commit history into a collection
git_repo_path = "../documenso"
repo = Repo(git_repo_path)
commits = list(repo.iter_commits('main', max_count=100))

git_collection_name = "git_commits"
if any(col.name == git_collection_name for col in existing_collections):
    git_collection = client.get_collection(name=git_collection_name)
else:
    git_collection = client.create_collection(name=git_collection_name)
for i, commit in enumerate(commits):
    message = commit.message.strip()
    date = commit.committed_datetime
    files = list(commit.stats.files.keys())
    diffs = []
    try:
        if commit.parents:
            diffs = commit.diff(commit.parents[0], create_patch=True)
        else:
            diffs = commit.diff(NULL_TREE, create_patch=True)  # optional: define NULL_TREE
    except Exception as e:
        print(f"Error generating diff for commit {commit.hexsha}: {e}")
        diffs = []

    diff_texts = []
    for diff in diffs:
        try:
            diff_texts.append(diff.diff.decode("utf-8", errors="ignore"))
        except Exception as e:
            print(f"Error decoding diff for file {diff.a_path or diff.b_path}: {e}")

    diff_combined = "\n".join(diff_texts)


    doc = f"""Commit message: {message}
      Date: {date}
      Files: {files}
      Diff:
      {diff_combined}
    """
    response = ollama.embed(model="mxbai-embed-large", input=doc)
    embeddings = response["embeddings"]
    git_collection.add(
            ids=[f"git_{i}"],
            embeddings=embeddings,
            documents=[doc]
        )

# Test questions and expected keywords
tests = [
  {
    "question": "do you know about this? -> optional fields in embeds, Fix optional fields blocking the signature process in embeds.",
    "expected_keywords": ""
  },
]

# Function to run RAG query from multiple collections
def query_rag_system(question):
    response = ollama.embed(model="mxbai-embed-large", input=question)
    embedded = response["embeddings"]

    docs_results = collection.query(query_embeddings=embedded, n_results=3)
    git_results = git_collection.query(query_embeddings=embedded, n_results=2)

    all_docs = [doc for sublist in docs_results["documents"] for doc in sublist]
    all_git_docs = [doc for sublist in git_results["documents"] for doc in sublist]

    context = "\n".join(all_docs + all_git_docs)
    prompt = f"Using this data: {context}. Respond to this prompt: {question}"
    output = ollama.generate(model="llama3.2", prompt=prompt)
    return output["response"]

# Evaluation loop
for test in tests:
    answer = query_rag_system(test["question"])
    print(f"\nQ: {test['question']}\nA: {answer.strip()}")
    matched = [kw for kw in test["expected_keywords"] if kw.lower() in answer.lower()]
    print(f"Matched Keywords: {matched} / {len(test['expected_keywords'])}")
