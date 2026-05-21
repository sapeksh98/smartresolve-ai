from utils.llm import ask_llm

def generate_resolution(category: str, complaint: str, policy: str) -> str:
    prompt = f"""
You are a strict customer support resolution specialist.

Your job is to suggest a resolution STRICTLY based on company policy.
Do NOT suggest refunds or compensation unless the policy explicitly allows it.
Do NOT over-promise anything not mentioned in the policy.

Category: {category}
Customer Complaint: {complaint}

Relevant Company Policy:
{policy}

Rules:
- If the issue is within normal policy limits, reassure the customer and give an update
- Only suggest refund if policy explicitly says customer is eligible
- Be realistic and policy-compliant
- Do not offer compensation unless policy mentions it

Format your response as:
RESOLUTION: <what should be done>
STEPS:
1. <step 1>
2. <step 2>
3. <step 3>
TIMELINE: <realistic timeline based on policy>
"""
    response = ask_llm(prompt)
    return response