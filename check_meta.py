"""Check if Chroma DB has doc_id and chunk_index metadata."""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import config

embeddings = HuggingFaceEmbeddings(
    model_name=config.EMBED_MODEL,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
vs = Chroma(
    collection_name=config.COLLECTION_NAME,
    embedding_function=embeddings,
    persist_directory=config.PERSIST_DIR,
)

count = vs._collection.count()
data = vs.get(limit=5, include=["metadatas", "documents"])

with open("D:/408RAG/check_output.txt", "w", encoding="utf-8") as f:
    f.write(f"Total chunks: {count}\n\n")
    for i, meta in enumerate(data["metadatas"]):
        f.write(f"--- Chunk {i} ---\n")
        f.write(f"  doc_id: {meta.get('doc_id', 'MISSING')}\n")
        f.write(f"  chunk_index: {meta.get('chunk_index', 'MISSING')}\n")
        f.write(f"  source: {meta.get('source', 'MISSING')}\n")
    f.write("\nDONE\n")
