from agents.classifier_agent import classify_ticket
from agents.rag_agent import get_relevant_policy
from agents.resolution_agent import generate_resolution
from agents.risk_agent import check_risk
from agents.response_writer_agent import write_customer_reply

complaint = "I ordered a laptop 2 weeks ago and still haven't received it. This is unacceptable!"

print("=" * 50)
print("STEP 1: Classifying ticket...")
classified = classify_ticket(complaint)
print(f"Category: {classified['category']}")
print(f"Priority: {classified['priority']}")
print(f"Summary: {classified['summary']}")

print("\n" + "=" * 50)
print("STEP 2: Retrieving relevant policy...")
policy = get_relevant_policy(classified["category"], complaint)
print(policy)

print("\n" + "=" * 50)
print("STEP 3: Generating resolution...")
resolution = generate_resolution(classified["category"], complaint, policy)
print(resolution)

print("\n" + "=" * 50)
print("STEP 4: Checking risk...")
risk = check_risk(classified["category"], complaint, classified["priority"])
print(f"Risk Level: {risk.get('risk_level')}")
print(f"Risk Reason: {risk.get('risk_reason')}")
print(f"Recommendation: {risk.get('recommendation')}")

print("\n" + "=" * 50)
print("STEP 5: Writing customer reply...")
reply = write_customer_reply(complaint, resolution, risk)
print(reply)

print("\n" + "=" * 50)
print("SUCCESS: All 5 agents working successfully!")