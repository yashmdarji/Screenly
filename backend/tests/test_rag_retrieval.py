import unittest
from backend.app.services.vector_store import InMemoryVectorStore
from backend.app.services.rag_engine import rag_engine


class TestRAGRetrieval(unittest.TestCase):
    def test_chunker_and_overlap(self):
        store = InMemoryVectorStore(chunk_size=100, chunk_overlap=30)
        long_text = (
            "Machine learning focuses on learning from experience. "
            "Artificial neural networks utilize backpropagation and gradient descent. "
            "Support vector machines maximize the geometric margin using hyperplanes. "
            "Decision trees split nodes using information gain and entropy."
        )
        chunks = store.chunker.chunk_text(long_text)
        self.assertGreaterEqual(len(chunks), 2)
        for c in chunks:
            self.assertGreater(len(c), 0)

    def test_rag_retrieval_grounding(self):
        results = rag_engine.retrieve_grounded_context(
            query="backpropagation gradient descent momentum",
            target_role="AI/ML Engineer",
            top_k=2
        )
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertIn("book_title", top)
        self.assertIn("similarity_score", top)
        self.assertGreater(top["similarity_score"], 0.04)
        self.assertGreater(len(top["text"]), 20)

    def test_backend_rag_retrieval(self):
        results = rag_engine.retrieve_grounded_context(
            query="B-trees LSM-trees database indexing cache-aside",
            target_role="Backend Engineer",
            top_k=2
        )
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertIn("book_title", top)
        self.assertIn("text", top)


if __name__ == "__main__":
    unittest.main()
