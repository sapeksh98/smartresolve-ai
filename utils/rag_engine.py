import os
import pickle
import re
import numpy as np
from dotenv import load_dotenv

load_dotenv()

TFIDF_INDEX_PATH = "data/tfidf_index.pkl"

def tokenize(text: str) -> list:
    # Lowercase and split into alphanumeric tokens
    return re.findall(r'\w+', text.lower())

def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 100) -> list:
    chunks = []
    if len(text) <= chunk_size:
        return [text]
    
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break
            
        boundary = -1
        for sep in ["\n\n", "\n", ". ", " "]:
            idx = text.rfind(sep, start, end)
            if idx != -1 and idx > start + chunk_overlap:
                boundary = idx + len(sep)
                break
        
        if boundary != -1:
            chunks.append(text[start:boundary])
            start = boundary - chunk_overlap
        else:
            chunks.append(text[start:end])
            start = end - chunk_overlap
            
    print(f"[RAG] Created {len(chunks)} chunks")
    return chunks

class FAISSRetriever:
    """
    Named FAISSRetriever to maintain backwards compatibility with imports in main.py,
    but implements a lightweight TF-IDF indexing/retrieval engine.
    """
    def __init__(self):
        self.chunks = []
        self.vocab = {}
        self.idf = []
        self.chunk_vectors = []
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
        return os.path.exists(TFIDF_INDEX_PATH)

    def _build_index(self, policy_path: str = "data/company_policies.txt"):
        print("[RAG] Building TF-IDF index...")
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
            with open(policy_path, "w", encoding="utf-8") as f:
                f.write(default_policy)
            print("[RAG] Created default policy file")

        with open(policy_path, "r", encoding="utf-8") as f:
            text = f.read()

        self.chunks = chunk_text(text)
        if not self.chunks:
            self.chunks = [""]

        # Build vocabulary
        all_tokens_per_chunk = [tokenize(c) for c in self.chunks]
        vocab_set = set()
        for tokens in all_tokens_per_chunk:
            vocab_set.update(tokens)
        
        self.vocab = {word: idx for idx, word in enumerate(sorted(vocab_set))}
        vocab_size = len(self.vocab)
        num_docs = len(self.chunks)

        if vocab_size == 0:
            self.vocab = {"placeholder": 0}
            vocab_size = 1
            all_tokens_per_chunk = [["placeholder"] for _ in self.chunks]

        # Calculate IDF
        df = np.zeros(vocab_size)
        for tokens in all_tokens_per_chunk:
            unique_tokens = set(tokens)
            for t in unique_tokens:
                if t in self.vocab:
                    df[self.vocab[t]] += 1
        
        # Smooth IDF
        self.idf = np.log((num_docs + 1) / (df + 1)) + 1

        # Calculate TF-IDF vectors for all chunks
        self.chunk_vectors = []
        for tokens in all_tokens_per_chunk:
            tf = np.zeros(vocab_size)
            for t in tokens:
                if t in self.vocab:
                    tf[self.vocab[t]] += 1
            vector = tf * self.idf
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            self.chunk_vectors.append(vector)
        
        self.chunk_vectors = np.array(self.chunk_vectors)

        # Save to disk
        data = {
            "chunks": self.chunks,
            "vocab": self.vocab,
            "idf": self.idf,
            "chunk_vectors": self.chunk_vectors
        }
        with open(TFIDF_INDEX_PATH, "wb") as f:
            pickle.dump(data, f)
        print(f"[RAG] Index saved! {len(self.chunks)} chunks, vocab_size={vocab_size}")

    def _load_index(self):
        print("[RAG] Loading TF-IDF index from disk...")
        with open(TFIDF_INDEX_PATH, "rb") as f:
            data = pickle.load(f)
        self.chunks = data["chunks"]
        self.vocab = data["vocab"]
        self.idf = data["idf"]
        self.chunk_vectors = data["chunk_vectors"]
        print(f"[RAG] Loaded {len(self.chunks)} chunks.")

    def rebuild(self, policy_path: str = "data/company_policies.txt"):
        if os.path.exists(TFIDF_INDEX_PATH):
            os.remove(TFIDF_INDEX_PATH)
        self._initialized = False
        self._build_index(policy_path)
        self._initialized = True

    def retrieve(self, query: str, top_k: int = 3) -> list:
        if not self._initialized:
            self.initialize()
        
        if not self.chunks or len(self.vocab) == 0:
            return []

        query_tokens = tokenize(query)
        vocab_size = len(self.vocab)
        
        # Calculate query TF-IDF vector
        query_tf = np.zeros(vocab_size)
        for t in query_tokens:
            if t in self.vocab:
                query_tf[self.vocab[t]] += 1
        
        query_vector = query_tf * self.idf
        query_norm = np.linalg.norm(query_vector)
        if query_norm > 0:
            query_vector = query_vector / query_norm

        # Cosine similarity
        similarities = np.dot(self.chunk_vectors, query_vector)

        # Get top k
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for i, idx in enumerate(top_indices):
            results.append({
                "chunk": self.chunks[idx],
                "score": round(float(similarities[idx]), 4),
                "rank": i + 1
            })
        return results

retriever = FAISSRetriever()