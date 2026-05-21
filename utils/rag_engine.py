import os
import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()

FAISS_INDEX_PATH = "data/faiss_index.bin"
CHUNKS_PATH = "data/chunks.pkl"

# Free local embedding model — no API needed
embedder = SentenceTransformer("all-MiniLM-L6-v2")
print("[RAG] Embedding model loaded: all-MiniLM-L6-v2")

def get_embedding(text: str) -> list:
    return embedder.encode(text).tolist()

def chunk_text(text: str) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_text(text)
    print(f"[RAG] Created {len(chunks)} chunks")
    return chunks

class FAISSRetriever:
    def __init__(self, policy_path: str = "data/company_policies.txt"):
        self.chunks = []
        self.index = None
        self.policy_path = policy_path

        # Restore from default_policies.txt if missing (e.g. Render volume overlay)
        if not os.path.exists(self.policy_path):
            os.makedirs(os.path.dirname(self.policy_path), exist_ok=True)
            if os.path.exists("default_policies.txt"):
                import shutil
                shutil.copy("default_policies.txt", self.policy_path)
                print("[RAG] Restored default policy file from backup.")
            else:
                with open(self.policy_path, "w") as f:
                    f.write("Company Policy Document\n")
                print("[RAG] Created empty policy file.")

        if self._index_exists():
            self._load_index()
        else:
            self._build_index()

    def _index_exists(self) -> bool:
        return (
            os.path.exists(FAISS_INDEX_PATH) and
            os.path.exists(CHUNKS_PATH)
        )

    def _build_index(self):
        print("[RAG] Building FAISS index...")
        with open(self.policy_path, "r") as f:
            text = f.read()

        self.chunks = chunk_text(text)

        print("[RAG] Generating embeddings...")
        # Batch embed all chunks at once — much faster!
        embeddings = embedder.encode(self.chunks, show_progress_bar=True)

        matrix = np.array(embeddings).astype("float32")
        dim = matrix.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(matrix)

        faiss.write_index(self.index, FAISS_INDEX_PATH)
        with open(CHUNKS_PATH, "wb") as f:
            pickle.dump(self.chunks, f)

        print(f"[RAG] Index saved! {len(self.chunks)} chunks, dim={dim}")

    def _load_index(self):
        print("[RAG] Loading FAISS index from disk...")
        self.index = faiss.read_index(FAISS_INDEX_PATH)
        with open(CHUNKS_PATH, "rb") as f:
            self.chunks = pickle.load(f)
        print(f"[RAG] Loaded {len(self.chunks)} chunks.")

    def rebuild(self):
        for path in [FAISS_INDEX_PATH, CHUNKS_PATH]:
            if os.path.exists(path):
                os.remove(path)
        self._build_index()

    def retrieve(self, query: str, top_k: int = 3) -> list:
        query_emb = np.array([get_embedding(query)]).astype("float32")
        distances, indices = self.index.search(query_emb, top_k)
        results = []
        for i, idx in enumerate(indices[0]):
            results.append({
                "chunk": self.chunks[idx],
                "score": round(float(distances[0][i]), 4),
                "rank": i + 1
            })
        return results

retriever = FAISSRetriever()