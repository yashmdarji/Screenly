import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.app.config import KNOWLEDGE_BASE_DIR, settings
from backend.app.services.vector_store import InMemoryVectorStore


class RAGEngine:
    """
    Orchestrates Knowledge Ingestion, Dynamic Query Construction,
    and Grounded Context Retrieval.
    """

    def __init__(self):
        self.vector_store = InMemoryVectorStore(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        self.indexed_books = []
        self._initialize_knowledge_base()

    def _initialize_knowledge_base(self):
        """Loads and indexes all role-specific JSON knowledge files."""
        if not KNOWLEDGE_BASE_DIR.exists():
            return

        json_files = list(KNOWLEDGE_BASE_DIR.glob("**/*.json"))
        for file_path in json_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                book_title = data.get("book_title", file_path.stem)
                author = data.get("author", "Unknown Author")
                role = data.get("role", "General")

                self.indexed_books.append({
                    "title": book_title,
                    "author": author,
                    "role": role,
                    "file": str(file_path.name)
                })

                for chapter in data.get("chapters", []):
                    ch_num = chapter.get("chapter_number")
                    ch_title = chapter.get("chapter_title")

                    for section in chapter.get("sections", []):
                        sec_id = section.get("section_id")
                        sec_title = section.get("section_title")
                        content = section.get("content", "")

                        self.vector_store.add_document(
                            text=content,
                            role=role,
                            book_title=book_title,
                            author=author,
                            chapter_number=ch_num,
                            chapter_title=ch_title,
                            section_id=sec_id,
                            section_title=sec_title,
                        )
            except Exception as e:
                print(f"[RAGEngine] Error loading {file_path}: {e}")

        self.vector_store.build_index()
        print(f"[RAGEngine] Successfully indexed {len(self.vector_store.chunks)} chunks across {len(self.indexed_books)} books.")

    def construct_queries_for_candidate(
        self,
        target_role: str,
        parsed_skills: List[str],
        domains: List[str]
    ) -> List[Dict[str, str]]:
        """
        Synthesizes candidate profile + target role into specific, meaningful queries
        to retrieve grounded concepts from the knowledge base.
        """
        queries = []

        if "AI" in target_role or "ML" in target_role:
            # Query 1: Optimization and Neural Foundations
            queries.append({
                "topic": "Neural Architectures & Optimization",
                "query": f"artificial neural networks backpropagation gradient descent momentum local minima {' '.join(parsed_skills[:4])}"
            })
            # Query 2: Generalization & Model Selection
            queries.append({
                "topic": "Generalization & Overfitting Control",
                "query": "overfitting bias variance tradeoff L1 L2 regularization cross validation data leakage"
            })
            # Query 3: Classical ML & Theory
            queries.append({
                "topic": "Statistical Learning & SVMs",
                "query": "support vector machines maximum margin kernel trick decision trees information gain entropy"
            })
            # Query 4: Evaluation & Ensembles
            queries.append({
                "topic": "Ensemble Methods & Loss Optimization",
                "query": "bagging random forests gradient boosting residual minimization precision recall ROC-AUC"
            })
            # Query 5: Probabilistic / PAC Foundations
            queries.append({
                "topic": "Bayesian Estimation & VC Dimension",
                "query": "Bayes theorem maximum a posteriori MAP naive bayes conditional independence PAC learning VC dimension"
            })

        elif "Backend" in target_role:
            # Query 1: Data Storage & Indexing
            queries.append({
                "topic": "Storage Engines & Index Optimization",
                "query": f"B-trees LSM trees storage indexing query optimization EXPLAIN ANALYZE {' '.join(parsed_skills[:3])}"
            })
            # Query 2: Caching Architecture
            queries.append({
                "topic": "Caching Strategy & Concurrency",
                "query": "cache-aside write-through write-behind cache stampede thundering herd invalidation"
            })
            # Query 3: Transactions & Concurrency Control
            queries.append({
                "topic": "ACID Transactions & Isolation Levels",
                "query": "ACID isolation levels dirty reads repeatable read MVCC distributed locks fencing tokens idempotency"
            })
            # Query 4: Distributed Systems & Consensus
            queries.append({
                "topic": "Distributed Consensus & CAP Trade-offs",
                "query": "CAP theorem eventual consistency partition tolerance replication CRDT"
            })
            # Query 5: Microservices & Messaging
            queries.append({
                "topic": "API Architecture & Message Streaming",
                "query": "microservices REST gRPC HTTP/2 protocol buffers Kafka RabbitMQ event-driven outbox pattern"
            })

        else:
            # Data Science / General
            queries.append({
                "topic": "Evaluation Metrics for Imbalanced Data",
                "query": "precision recall F1-score PR-AUC imbalanced classification SMOTE cost-sensitive"
            })
            queries.append({
                "topic": "Feature Engineering & Selection",
                "query": "target encoding high-cardinality feature selection mutual information recursive feature elimination"
            })
            queries.append({
                "topic": "Model Validation & Cross-Validation",
                "query": "k-fold cross-validation data leakage bias-variance tradeoff regularization"
            })
            queries.append({
                "topic": "Ensemble Learning & Gradient Boosting",
                "query": "random forest bagging gradient boosted trees XGBoost decision tree"
            })
            queries.append({
                "topic": "Statistical Foundations & Hypotheses",
                "query": "Bayes theorem naive bayes conditional independence hypothesis testing"
            })

        return queries

    def retrieve_grounded_context(
        self,
        query: str,
        target_role: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Queries the vector store and returns top-k grounded chunks."""
        results = self.vector_store.similarity_search(
            query=query,
            role=target_role,
            top_k=top_k,
            min_threshold=0.04
        )

        # Fallback if specific role filter is too strict: search across all books
        if not results:
            results = self.vector_store.similarity_search(
                query=query,
                role=None,
                top_k=top_k,
                min_threshold=0.01
            )

        return results

    def get_knowledge_summary(self) -> Dict[str, Any]:
        """Returns metadata about loaded knowledge base."""
        return {
            "total_chunks": len(self.vector_store.chunks),
            "indexed_books": self.indexed_books,
            "vocabulary_size": len(self.vector_store.vocabulary)
        }


# Global singleton RAG instance
rag_engine = RAGEngine()
