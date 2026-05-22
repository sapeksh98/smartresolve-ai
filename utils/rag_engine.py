import os
import faiss
import numpy as np
import pickle
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()

FAISS_INDEX_PATH = "data/faiss_index.bin"
CHUNKS_PATH = "data/chunks.pkl"

# Don't load model at import time!
embedder = None

def get_embedder():
    global embedder
    if embedder is None:
        print("[RAG] Loading embedding model...")
        from sentence_transformers import SentenceTransformer
        embedder = SentenceTransformer(
            "paraphrase-MiniLM-L3-v2",
            cache_folder="data/model_cache"
        )
        print("[RAG] Model loaded!")
    return embedder

def get_embedding(text: str) -> list:
    return get_embedder().encode(text).tolist()

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
    def __init__(self):
        self.chunks = []
        self.index = None
        self._initialized = False

    def initialize(self, policy_path: str = "data/company_policies.txt"):
        if self._initialized:
            return
        if self._index_exists():
            self._load_index()
        else:
            self._build_index(policy_path)
        self._initialized = True

    def _index_exists(self) -> bool:
        return (
            os.path.exists(FAISS_INDEX_PATH) and
            os.path.exists(CHUNKS_PATH)
        )

    def _build_index(self, policy_path: str = "data/company_policies.txt"):
        print("[RAG] Building FAISS index...")
        os.makedirs("data", exist_ok=True)

        if not os.path.exists(policy_path):
            # Create default policy if none exists
            default_policy = """REFUND POLICY:
Customers can request a full refund within 30 days of purchase.
Refunds are processed within 5-7 business days.
Digital products are non-refundable after download.

DELIVERY POLICY:
Standard delivery takes 5-7 business days.
Express delivery takes 1-2 business days.
If delivery exceeds 14 days, customer is eligible for full refund.
Lost packages are replaced at no extra cost within 30 days.

BILLING POLICY:
Customers are billed on the 1st of every month for subscriptions.
Duplicate charges are refunded within 3 business days.
Billing disputes must be raised within 60 days of transaction.

TECHNICAL SUPPORT POLICY:
Technical issues must be reported within 90 days of purchase.
Free support is provided for 1 year after purchase.

SUBSCRIPTION POLICY:
Subscriptions can be cancelled anytime before next billing cycle.
Annual plans are non-refundable after 7 day trial period.

COMPLAINT POLICY:
All complaints are acknowledged within 24 hours.
Resolution is provided within 3-5 business days.
Compensation may be offered for service failures.
"""
            with open(policy_path, "w") as f:
                f.write(default_policy)
            print("[RAG] Created default policy file")

        with open(policy_path, "r") as f:
            text = f.read()

        self.chunks = chunk_text(text)

        print("[RAG] Generating embeddings...")
        emb = get_embedder()
        embeddings = emb.encode(self.chunks, show_progress_bar=True)

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

    def rebuild(self, policy_path: str = "data/company_policies.txt"):
        for path in [FAISS_INDEX_PATH, CHUNKS_PATH]:
            if os.path.exists(path):
                os.remove(path)
        self._initialized = False
        self._build_index(policy_path)
        self._initialized = True

    def retrieve(self, query: str, top_k: int = 3) -> list:
        if not self._initialized:
            self.initialize()
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

# Don't initialize at import time!
retriever = FAISSRetriever()