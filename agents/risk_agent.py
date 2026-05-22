from utils.llm import ask_llm
from utils.scoring import calculate_risk
import json
import re

def extract_json(text: str) -> dict:
    try:
        return json.loads(text.strip())
    except:
        pass
    try:
        clean = re.sub(r'```json|```', '', text).strip()
        return json.loads(clean)
    except:
        pass
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        pass
    return None

def check_risk(category: str, complaint: str, priority: str) -> dict:
    risk_data = calculate_risk(category, complaint, priority)


    prompt = f"""
You are a risk assessment specialist.
Respond ONLY with a valid JSON object. No explanation, no markdown, no extra text.

Category: {category}
Complaint: {complaint}
Risk Level: {risk_data["risk_level"]}

Return exactly this JSON:
{{
  "risk_reason": "brief explanation of risk",
  "recommendation": "specific action to take"
}}
"""
    for attempt in range(3):
        try:
            response = ask_llm(prompt)
            result = extract_json(response)
            if result and "risk_reason" in result:
                return {
                    "risk_level": risk_data["risk_level"],
                    "risk_score": risk_data["risk_score"],
                    "should_escalate": risk_data["should_escalate"],
                    "risk_reason": result.get("risk_reason", ""),
                    "recommendation": result.get("recommendation", "")
                }
        except Exception as e:
            print(f"[Risk] Attempt {attempt+1} failed: {e}")

    # Final fallback
    return {
        "risk_level": risk_data["risk_level"],
        "risk_score": risk_data["risk_score"],
        "should_escalate": risk_data["should_escalate"],
        "risk_reason": "Risk assessed based on complaint analysis.",
        "recommendation": "Manual review recommended."
    }