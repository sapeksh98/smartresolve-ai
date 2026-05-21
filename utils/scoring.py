import re

CATEGORY_WEIGHTS = {
    "REFUND": 30,
    "BILLING": 25,
    "COMPLAINT": 25,
    "TECHNICAL": 20,
    "DELIVERY": 20,
    "SUBSCRIPTION": 15,
    "GENERAL": 10
}

HIGH_PRIORITY_KEYWORDS = [
    "urgent", "immediately", "lawsuit", "fraud", "scam",
    "unacceptable", "furious", "disgusting", "terrible",
    "worst", "never again", "lawyer", "police", "report"
]

MEDIUM_PRIORITY_KEYWORDS = [
    "waiting", "delayed", "issue", "problem", "not working",
    "disappointed", "frustrated", "wrong", "incorrect", "missing"
]

LOW_PRIORITY_KEYWORDS = [
    "question", "curious", "wondering", "when will",
    "would like", "could you", "please", "kindly"
]

NEGATIVE_WORDS = [
    "angry", "frustrated", "terrible", "horrible", "awful",
    "disgusting", "furious", "outraged", "unacceptable",
    "worst", "useless", "pathetic", "ridiculous", "absurd"
]

def calculate_priority(complaint: str) -> dict:
    text = complaint.lower()
    score = 0

    for kw in HIGH_PRIORITY_KEYWORDS:
        if kw in text:
            score += 3
    for kw in MEDIUM_PRIORITY_KEYWORDS:
        if kw in text:
            score += 2
    for kw in LOW_PRIORITY_KEYWORDS:
        if kw in text:
            score += 1

    if len(complaint.split()) < 8:
        score = max(0, score - 2)

    if score >= 5:
        priority = "HIGH"
    elif score >= 2:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    return {"priority": priority}


def calculate_risk(category: str, complaint: str, priority: str) -> dict:
    text = complaint.lower()
    score = 0

    score += CATEGORY_WEIGHTS.get(category, 10)

    priority_weights = {"HIGH": 30, "MEDIUM": 20, "LOW": 10}
    score += priority_weights.get(priority, 10)

    neg_count = sum(1 for w in NEGATIVE_WORDS if w in text)
    score += min(neg_count * 5, 20)

    if re.search(r'\$[\d,]+|[\d,]+\s*(dollar|usd|rs|rupee)', text):
        score += 10

    if any(w in text for w in ["lawsuit", "lawyer", "court", "legal", "police"]):
        score += 20

    if re.search(r'\d+\s*(week|month|day)', text):
        score += 5

    score = min(score, 100)

    if score >= 70:
        risk_level = "HIGH"
        should_escalate = True
    elif score >= 40:
        risk_level = "MEDIUM"
        should_escalate = False
    else:
        risk_level = "LOW"
        should_escalate = False

    return {
        "risk_level": risk_level,
        "should_escalate": should_escalate
    }