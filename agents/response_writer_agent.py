from utils.llm import ask_llm

def write_customer_reply(complaint: str, resolution: str, risk: dict) -> str:
    prompt = f"""
You are a professional customer support representative.

Write a polite, empathetic, and professional email reply to the customer.

Customer Complaint: {complaint}
Resolution Plan: {resolution}
Risk Level: {risk.get("risk_level", "LOW")}

Rules:
- Be empathetic and apologetic
- Be clear about what will happen next
- Keep it under 150 words
- End with a positive note
- Do not mention internal risk assessments

Write only the email body, no subject line.
"""
    response = ask_llm(prompt)
    return response