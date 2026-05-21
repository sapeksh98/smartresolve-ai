from agents.classifier_agent import classify_ticket

complaint = "I ordered a laptop 2 weeks ago and still haven't received it. This is unacceptable!"

result = classify_ticket(complaint)
print("Category:", result["category"])
print("Priority:", result["priority"])
print("Summary:", result["summary"])