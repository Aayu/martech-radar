import re
import unicodedata


FMCG = ["coca-cola", "coca cola", "diet coke", "pepsico", "pepsi", "unilever", "p&g", "procter & gamble",
        "reckitt", "nestle", "mondelez", "l'oreal", "l’oréal", "colgate", "mars", "danone", "haleon",
        "tata consumer", "itc", "godrej", "marico", "cadbury", "dove", "oreo", "hellmann", "clorox", "hershey"]
ENTERPRISE = ["walmart", "target", "amazon", "albertsons", "nike", "starbucks", "mcdonald", "disney",
              "marriott", "hilton", "american express", "samsung", "jd sports", "wayfair", "sainsbury", "tesco"]
TOPICS = {
    "Customer data": ["customer data", "first-party", "first party", "identity resolution", "cdp", "clean room", "consent"],
    "Lifecycle and loyalty": ["loyalty", "crm", "retention", "personalization", "personalisation", "lifecycle", "segmentation", "rewards"],
    "Commerce and measurement": ["commerce", "ecommerce", "e-commerce", "retail media", "digital shelf", "incrementality", "attribution", "conversion", "checkout", "marketplace", "shopping", "experiment"],
    "Connected journey": ["connected packaging", "qr code", "omnichannel", "journey", "receipt", "pack scan", "verification", "activation", "campaign", "in-store", "mobile app"],
    "AI implementation": ["ai", "artificial intelligence", "generative ai", "agentic", "ai agent", "decisioning", "recommendation engine", "machine learning"],
    "Regulation and operations": ["privacy", "data protection", "deprecat", "regulat", "erasure", "migration", "incident", "outage"],
}


def normalize(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))


def contains(text, token):
    return bool(re.search(r"(?<!\w)" + re.escape(normalize(token)) + (r"(?!\w)" if len(token) < 5 else ""), text))


def rank(title, text, source):
    # These are transparent triage points, NOT the editorial 20-point evidence score.
    body = normalize(title + " " + text)
    heading = normalize(title)
    companies = [c for c in FMCG + ENTERPRISE if contains(body, c)]
    topics = [label for label, words in TOPICS.items() if any(contains(body, w) for w in words)]
    beats = []
    if any(c in FMCG for c in companies) or "fmcg" in source.get("beats", []):
        beats.append("FMCG")
    if any(c in ENTERPRISE for c in companies) or "enterprise" in source.get("beats", []):
        beats.append("Enterprise")
    if "Connected journey" in topics or "journey" in source.get("beats", []):
        beats.append("Journey candidate")
    points = min(100, 12 * len(topics) + (15 if companies else 0) +
                 8 * sum(any(contains(heading, w) for w in words) for words in TOPICS.values()) +
                 (8 if re.search(r"case study|how |experiment|implemented|migration|results", heading) else 0))
    if re.search(r"appoints|names .* officer|raises .*million|funding round|sponsored webinar", heading):
        points = max(0, points - 25)
    evidence = "Vendor/brand account" if source.get("kind") in ("brand", "platform", "case_library") else "Unreviewed reporting"
    if "sponsored" in body[:1200] or "partner content" in body[:1200]:
        evidence = "Sponsored content — review claims"
    reason = ", ".join(topics) or "Needs relevance review"
    return {"priority": points, "tags": topics, "companies": companies, "beats": beats,
            "evidence": evidence, "reason": reason}

