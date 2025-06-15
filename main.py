import ollama
import chromadb

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
    # store each document in a vector embedding database
    for i, d in enumerate(documents):
        response = ollama.embed(model="mxbai-embed-large", input=d)
        embeddings = response["embeddings"]
        collection.add(
            ids=[str(i)],
            embeddings=embeddings,
            documents=[d]
        )

# Test questions and expected keywords
tests = [
  {
    "question": "Why do people ignore conflicting information?",
    "expected_keywords": ["confirmation bias", "cognitive dissonance", "beliefs"]
  },
  {
    "question": "What happens to the body during stress?",
    "expected_keywords": ["fight or flight", "heart rate", "adrenaline"]
  },
  {
    "question": "Are humans social creatures?",
    "expected_keywords": ["connection", "group", "evolution", "belonging"]
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
