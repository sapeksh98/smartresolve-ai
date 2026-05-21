from utils.llm import ask_llm
from utils.scoring import calculate_priority
import json
import re

def extract_json(text: str) -> dict:
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except:
        pass

    # Try stripping markdown code blocks
    try:
        clean = re.sub(r'```json|```', '', text).strip()
        return json.loads(clean)
    except:
        pass

    # Try extracting just the JSON object
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        pass

    return None

def classify_ticket(complaint: str) -> dict:
    prompt = f"""
You are a customer support ticket classifier.
Respond ONLY with a valid JSON object. No explanation, no markdown, no extra text.

Classify this complaint:
"{complaint}"

Return exactly this JSON:
{{
  "category": "REFUND|BILLING|DELIVERY|TECHNICAL|COMPLAINT|SUBSCRIPTION",
  "summary": "one sentence summary",
  "confidence": 0.0 to 1.0
}}
"""
    # Retry up to 3 times
    for attempt in range(3):
        try:
            response = ask_llm(prompt)
            result = extract_json(response)
            if result and "category" in result:
                priority_data = calculate_priority(complaint)
                result["priority"] = priority_data["priority"]
                return result
        except Exception as e:
            print(f"[Classifier] Attempt {attempt+1} failed: {e}")

    # Final fallback
    priority_data = calculate_priority(complaint)
    return {
        "category": "GENERAL",
        "summary": "Customer complaint received.",
        "confidence": 0.5,
        "priority": priority_data["priority"]
    }