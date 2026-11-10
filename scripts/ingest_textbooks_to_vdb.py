"""
Screenly Offline Knowledge Ingestion Pipeline
Parses all 7 canonical textbooks from data/knowledge_base/,
generates semantic vector embeddings, and persists them into ChromaDB / Persistent Vector Database.
"""

import sys
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config import KNOWLEDGE_BASE_DIR, CHROMA_PERSIST_DIR
from backend.app.services.vector_store import PersistentVectorStore


CANONICAL_BOOKS = [
    "Machine Learning (Tom M. Mitchell)",
    "The Hundred-Page Machine Learning Book (Andriy Burkov)",
    "Machine Learning for Absolute Beginners (Oliver Theobald)",
    "Introduction to Machine Learning with Python (Andreas Müller & Sarah Guido)",
    "Master Machine Learning Algorithms (Jason Brownlee)",
    "Pattern Recognition and Machine Learning (Christopher M. Bishop)",
    "Artificial Intelligence, Machine Learning and Deep Learning Foundations"
]


def run_ingestion():
    print("=" * 70)
    print(" SCREENLY: CANONICAL TEXTBOOK VECTOR INGESTION PIPELINE")
    print("=" * 70)
    print(f"[*] Scanning Knowledge Base Directory: {KNOWLEDGE_BASE_DIR}")
    print(f"[*] Persistent Vector Database Target:  {CHROMA_PERSIST_DIR}")
    print("-" * 70)

    # Clean existing index file if re-indexing explicitly
    index_file = CHROMA_PERSIST_DIR / "vector_index.json"
    if index_file.exists():
        index_file.unlink()

    vdb = PersistentVectorStore(persist_dir=CHROMA_PERSIST_DIR)

    json_files = list(KNOWLEDGE_BASE_DIR.glob("**/*.json"))
    if not json_files:
        print("[!] No JSON textbook files found in knowledge base!")
        return

    total_books = 0
    total_sections = 0

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            book_title = data.get("book_title", file_path.stem)
            author = data.get("author", "Unknown Author")
            role = data.get("role", "General")
            chapters = data.get("chapters", [])

            book_sections = 0
            for chapter in chapters:
                ch_num = chapter.get("chapter_number")
                ch_title = chapter.get("chapter_title")

                for section in chapter.get("sections", []):
                    sec_id = section.get("section_id")
                    sec_title = section.get("section_title")
                    content = section.get("content", "")

                    vdb.add_document(
                        text=content,
                        role=role,
                        book_title=book_title,
                        author=author,
                        chapter_number=ch_num,
                        chapter_title=ch_title,
                        section_id=sec_id,
                        section_title=sec_title,
                    )
                    book_sections += 1

            total_books += 1
            total_sections += book_sections
            print(f"[+] Ingested: '{book_title}' by {author} ({len(chapters)} chapters, {book_sections} sections)")

        except Exception as e:
            print(f"[-] Failed to ingest {file_path.name}: {e}")

    print("-" * 70)
    print("[*] Generating normalized vector embeddings & computing vocabulary...")
    vdb.build_index()

    print("[*] Persisting vector database to disk...")
    vdb.save_to_disk()

    print("=" * 70)
    print(" INGESTION COMPLETE & PERSISTED TO DISK")
    print(f"[*] Total Books Ingested:       {total_books}")
    print(f"[*] Total Text Sections:        {total_sections}")
    print(f"[*] Total Vector Chunks Stored: {len(vdb.chunks)}")
    print(f"[*] Vocabulary Dimension:       {len(vdb.vocabulary)} terms")
    print(f"[*] Database Path:              {CHROMA_PERSIST_DIR}")
    print(f"[*] Index File:                 {index_file} ({index_file.stat().st_size / 1024:.2f} KB)")
    print("=" * 70)


if __name__ == "__main__":
    run_ingestion()
