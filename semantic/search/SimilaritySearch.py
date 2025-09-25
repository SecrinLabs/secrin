from semantic.VectorStore import VectorStore

class SimilaritySearch:
    def __init__(self, collection_name: str) -> None:
        self.vector_store = VectorStore(collection_name).get_vector_store()

    def get_similar_answer(self, question: str, k: int = 3):
        return self.vector_store.similarity_search(question, k=k)
    

