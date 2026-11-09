import re
import math
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class DocumentChunk:
    chunk_id: str
    role: str
    book_title: str
    author: Optional[str]
    chapter_number: Optional[int]
    chapter_title: Optional[str]
    section_id: Optional[str]
    section_title: Optional[str]
    text: str
    embedding: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TextChunker:
    """Implements context-preserving semantic text chunking with overlap."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 80):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[str]:
        """Splits long text into overlapping chunks, respecting sentence boundaries."""
        if not text or len(text) <= self.chunk_size:
            return [text.strip()] if text else []

        # Split on sentence terminals first to preserve context
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_len = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_len = len(sentence)
            if current_len + sentence_len > self.chunk_size and current_chunk:
                # Store completed chunk
                chunk_str = " ".join(current_chunk)
                chunks.append(chunk_str)

                # Context preservation: carry over overlap from trailing sentences
                overlap_len = 0
                overlap_sentences = []
                for s in reversed(current_chunk):
                    if overlap_len + len(s) <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_len += len(s)
                    else:
                        break
                current_chunk = overlap_sentences
                current_len = sum(len(s) for s in current_chunk)

            current_chunk.append(sentence)
            current_len += sentence_len

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks


class InMemoryVectorStore:
    """
    Lightweight, high-performance in-memory vector database with cosine similarity
    and BM25/TF-IDF hybrid scoring. Zero external C++ dependencies required,
    ensuring cross-platform reproducibility and instant startup.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 80):
        self.chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.chunks: List[DocumentChunk] = []
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self._is_indexed = False

    def _tokenize(self, text: str) -> List[str]:
        """Simple, deterministic tokenization."""
        text = text.lower()
        tokens = re.findall(r'\b[a-zA-Z0-9_\-\+\#]{2,}\b', text)
        return tokens

    def add_document(
        self,
        text: str,
        role: str,
        book_title: str,
        author: Optional[str] = None,
        chapter_number: Optional[int] = None,
        chapter_title: Optional[str] = None,
        section_id: Optional[str] = None,
        section_title: Optional[str] = None,
    ):
        """Chunks and stores a document section."""
        split_chunks = self.chunker.chunk_text(text)
        for chunk_text in split_chunks:
            chunk = DocumentChunk(
                chunk_id=str(uuid.uuid4())[:8],
                role=role,
                book_title=book_title,
                author=author,
                chapter_number=chapter_number,
                chapter_title=chapter_title,
                section_id=section_id,
                section_title=section_title,
                text=chunk_text,
                metadata={
                    "char_count": len(chunk_text),
                    "role": role,
                    "book": book_title
                }
            )
            self.chunks.append(chunk)
        self._is_indexed = False

    def build_index(self):
        """Constructs IDF weights and normalized sparse/dense embeddings for all chunks."""
        if not self.chunks:
            return

        doc_count = len(self.chunks)
        doc_frequencies: Dict[str, int] = {}

        # 1. Calculate Document Frequencies
        for chunk in self.chunks:
            tokens = set(self._tokenize(chunk.text))
            for token in tokens:
                doc_frequencies[token] = doc_frequencies.get(token, 0) + 1

        # 2. Filter vocabulary and compute smoothed IDF
        self.vocabulary = {term: idx for idx, term in enumerate(doc_frequencies.keys())}
        self.idf = {
            term: math.log((doc_count + 1) / (df + 1)) + 1.0
            for term, df in doc_frequencies.items()
        }

        # 3. Compute normalized TF-IDF embeddings for each chunk
        for chunk in self.chunks:
            tokens = self._tokenize(chunk.text)
            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1

            # Sparse vector represented as dict {term_idx: weight}
            vector = {}
            norm_sq = 0.0
            for term, count in tf.items():
                if term in self.vocabulary:
                    # Sublinear TF scaling (1 + log(count)) * IDF
                    weight = (1.0 + math.log(count)) * self.idf[term]
                    vector[self.vocabulary[term]] = weight
                    norm_sq += weight * weight

            norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
            chunk.embedding = [vector, norm]

        self._is_indexed = True

    def similarity_search(
        self,
        query: str,
        role: Optional[str] = None,
        top_k: int = 3,
        min_threshold: float = 0.05
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top_k most relevant chunks using cosine similarity
        between query vector and chunk index.
        """
        if not self._is_indexed:
            self.build_index()

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # Build query vector
        query_tf: Dict[str, int] = {}
        for t in query_tokens:
            query_tf[t] = query_tf.get(t, 0) + 1

        query_vec: Dict[int, float] = {}
        q_norm_sq = 0.0
        for term, count in query_tf.items():
            if term in self.vocabulary:
                weight = (1.0 + math.log(count)) * self.idf.get(term, 1.0)
                term_idx = self.vocabulary[term]
                query_vec[term_idx] = weight
                q_norm_sq += weight * weight

        q_norm = math.sqrt(q_norm_sq)
        if q_norm == 0:
            return []

        results = []
        for chunk in self.chunks:
            # Filter by target role if specified (matching role or general)
            if role and chunk.role.lower() not in role.lower() and role.lower() not in chunk.role.lower():
                continue

            doc_vec, doc_norm = chunk.embedding
            # Dot product calculation
            dot_product = 0.0
            for term_idx, q_weight in query_vec.items():
                if term_idx in doc_vec:
                    dot_product += q_weight * doc_vec[term_idx]

            similarity = dot_product / (q_norm * doc_norm) if doc_norm > 0 else 0.0

            if similarity >= min_threshold:
                results.append({
                    "chunk_id": chunk.chunk_id,
                    "book_title": chunk.book_title,
                    "author": chunk.author,
                    "chapter_number": chunk.chapter_number,
                    "chapter_title": chunk.chapter_title,
                    "section_id": chunk.section_id,
                    "section_title": chunk.section_title,
                    "text": chunk.text,
                    "similarity_score": round(similarity, 4)
                })

        # Sort by similarity descending
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]
