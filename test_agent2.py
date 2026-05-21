from agents.classifier_agent import classify_ticket
from agents.rag_agent import get_relevant_policy

complaint = "I ordered a laptop 2 weeks ago and still haven't received it!"

classified = classify_ticket(complaint)
print("Category:", classified["category"])

policy = get_relevant_policy(classified["category"], complaint)
print("\nRelevant Policy:")
print(policy)