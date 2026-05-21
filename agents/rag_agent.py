from utils.rag_engine import retriever
from utils.llm import ask_llm

def get_relevant_policy(category: str, complaint: str) -> str:
    query = f"{category} {complaint}"
    chunks = retriever.retrieve(query, top_k=3)

    context = "\n\n".join([c["chunk"] for c in chunks])

    prompt = f"""
You are a policy retrieval assistant.

Based on the customer complaint below, extract the most relevant policy rules from the context.
Be concise and only include what directly applies.

Category: {category}
Complaint: {complaint}

Policy Context:
{context}

Return only the relevant policy points as a short bullet list.
"""
    return ask_llm(prompt)