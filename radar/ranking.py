import re
import unicodedata
from datetime import datetime, timezone


COMPANIES = {
    "Coca-Cola": ["coca-cola", "coca cola", "diet coke"],
    "PepsiCo": ["pepsico", "pepsi"],
    "Unilever": ["unilever"],
    "Procter & Gamble": ["procter & gamble", "p&g"],
    "Reckitt": ["reckitt"],
    "Nestlé": ["nestle", "nestlé"],
    "Mondelēz": ["mondelez", "mondelēz"],
    "L’Oréal": ["l'oreal", "l’oréal", "loreal"],
    "Colgate-Palmolive": ["colgate-palmolive", "colgate palmolive", "colgate"],
    "Mars": ["mars inc", "mars incorporated", "mars petcare", "mars wrigley"],
    "Danone": ["danone"],
    "Haleon": ["haleon"],
    "Tata Consumer": ["tata consumer"],
    "ITC": ["itc limited", "itc ltd"],
    "Godrej Consumer": ["godrej consumer"],
    "Marico": ["marico"],
    "Walmart": ["walmart"],
    "Target": ["target corporation", "target corp", "target stores", "target's"],
    "Amazon": ["amazon"],
    "Nike": ["nike"],
    "Starbucks": ["starbucks"],
    "McDonald’s": ["mcdonald's", "mcdonalds", "mcdonald’s"],
    "Disney": ["disney"],
    "Marriott": ["marriott"],
    "Hilton": ["hilton"],
    "American Express": ["american express", "amex"],
    "Samsung": ["samsung"],
    "JD Sports": ["jd sports"],
    "Wayfair": ["wayfair"],
    "Adobe": ["adobe"],
    "Meta": ["meta ads", "meta advertising", "facebook ads", "instagram ads"],
    "Google": ["google ads", "google advertising", "performance max", "demand gen"],
    "Salesforce": ["salesforce"],
    "Shopify": ["shopify"],
    "The Trade Desk": ["the trade desk"],
    "TikTok": ["tiktok"],
}

FMCG_COMPANIES = {
    "Coca-Cola", "PepsiCo", "Unilever", "Procter & Gamble", "Reckitt", "Nestlé",
    "Mondelēz", "L’Oréal", "Colgate-Palmolive", "Mars", "Danone", "Haleon",
    "Tata Consumer", "ITC", "Godrej Consumer", "Marico",
}
ENTERPRISE_COMPANIES = {
    "Walmart", "Target", "Amazon", "Nike", "Starbucks", "McDonald’s", "Disney",
    "Marriott", "Hilton", "American Express", "Samsung", "JD Sports", "Wayfair",
}

TOPICS = {
    "Martech stack and operations": [
        "marketing automation", "experience platform", "content supply chain", "digital asset management",
        "dam", "campaign orchestration", "journey orchestration", "decisioning", "marketing workflow",
        "customer journey analytics", "journey optimizer", "marketo", "marketing cloud", "genstudio",
    ],
    "Customer data, identity and privacy": [
        "customer data", "first-party", "first party", "identity resolution", "customer data platform",
        "cdp", "data clean room", "clean room", "consent", "privacy", "data deletion", "erasure",
    ],
    "Lifecycle, loyalty and personalization": [
        "loyalty", "crm", "retention", "personalization", "personalisation", "lifecycle",
        "segmentation", "rewards", "customer lifetime value", "lifetime value",
    ],
    "Adtech and media infrastructure": [
        "adtech", "ad tech", "programmatic", "demand-side platform", "dsp", "supply-side platform",
        "ssp", "ad server", "media buying", "performance max", "demand gen", "conversion api",
        "retail media", "connected tv", "ctv", "media network", "ad retrieval", "ad ranking",
        "dynamic creative", "performance marketing",
        "meta ads", "google ads", "amazon ads", "sponsored products",
    ],
    "Digital commerce and discovery": [
        "commerce", "ecommerce", "e-commerce", "digital shelf", "checkout", "marketplace", "shopping",
        "merchant center", "agentic commerce", "product feed", "product data", "search recommendations",
        "social commerce",
    ],
    "Connected consumer journey": [
        "connected packaging", "qr code", "omnichannel", "receipt", "pack scan", "verification",
        "in-store", "mobile app", "shoppable", "interactive video", "rewards app", "digital wallet",
    ],
    "Measurement and experimentation": [
        "incrementality", "attribution", "conversion", "conversions", "measuring", "experiment", "holdout", "marketing mix model",
        "mmm", "return on ad spend", "roas", "measurement framework", "causal", "brand lift",
        "conversion lift", "new-to-brand",
    ],
    "AI implementation and governance": [
        "artificial intelligence", "generative ai", "agentic", "ai agent", "recommendation engine",
        "machine learning", "ai-powered", "ai-driven", "llm", "large language model",
        "ai ads", "ai audience", "ai creative", "ai shopping", "ai search",
    ],
    "Regulation and standards": [
        "data protection", "regulation", "regulatory", "law", "rule", "standard", "framework",
        "public comment", "digital markets act", "digital services act", "dpdp", "gdpr", "ftc",
    ],
}

OUTCOME_RE = re.compile(
    r"(?:\b(?:lift\w*|incremental|conversion|seller intent|engagement|revenue|sales|roas|return on ad spend|"
    r"time saved|cost|increas\w*|decreas\w*|reduc\w*|improv\w*|growth)\b.{0,55}"
    r"\b\d+(?:\.\d+)?\s*(?:%|x|fold)|\b\d+(?:\.\d+)?\s*(?:%|x|fold).{0,55}"
    r"\b(?:lift|incremental|conversion|seller intent|engagement|revenue|sales|roas|growth)\b)"
)
IMPLEMENTATION_RE = re.compile(
    r"\b(?:implemented|deployed|scaled|scaling|rolled out|launch(?:ed)?|built|builds|use|uses|using|"
    r"migrated|integrated|in production|expanded to|available to all|open beta)\b"
)
PILOT_RE = re.compile(r"\b(?:pilot|pilots|testing|trial|proof of concept|beta)\b")
MECHANISM_RE = re.compile(
    r"\b(?:api|architecture|workflow|model|engine|platform|first-party data|customer data|product feed|"
    r"clean room|identity|orchestration|decisioning|attribution|incrementality|holdout|agents?|"
    r"content supply chain|dynamic creative|retail media|programmatic|dsp|conversion api|agentic commerce)\b"
)
FAILURE_RE = re.compile(
    r"\b(?:hurt results?|failed|failure|unapproved|without consent|outage|misleading|fraud|bias|"
    r"brand safety|measurement gap|cannot measure|can't measure|does not work|didn't work|backfire)\b"
)
STANDARD_RE = re.compile(
    r"\b(?:framework|standard|specification|protocol|regulation|regulatory|law|rule|guidance|"
    r"public comment|enforcement|consent order)\b"
)
PLATFORM_SHIFT_RE = re.compile(
    r"\b(?:rolls? out|launch(?:es|ed)?|builds? infrastructure|product data|new ad formats?|sunset|"
    r"auto-upgrade|agentic commerce|full-funnel campaigns?|measurement standard|conversion api)\b"
)
GENERIC_RE = re.compile(
    r"\b(?:summit|conference|webinar|roundup|spotlight interviews?|trends? to watch|debate|discuss|"
    r"should you|what marketers need to know|opinion)\b"
)
PARTNERSHIP_RE = re.compile(r"\b(?:partners? with|partnership|strategic alliance|collaborat(?:e|es|ion))\b")
CORPORATE_RE = re.compile(r"\b(?:appoints|names? .{0,30} officer|raises? .{0,15}million|funding round)\b")


def normalize(text):
    return "".join(c for c in unicodedata.normalize("NFKD", (text or "").lower()) if not unicodedata.combining(c))


def contains(text, token):
    return bool(re.search(r"(?<!\w)" + re.escape(normalize(token)) + r"(?!\w)", text))


def _company_hits(heading, body):
    hits = []
    # The opening section is enough for the subject. This avoids company names in
    # footers and related-story modules becoming false positives.
    subject_text = heading + " " + body[:6000]
    for company, aliases in COMPANIES.items():
        if any(contains(subject_text, alias) for alias in aliases):
            hits.append(company)
    return hits


def _freshness_penalty(published, now):
    if not published:
        return 0
    try:
        value = datetime.fromisoformat(str(published).replace("Z", "+00:00"))
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return 0
    now = now or datetime.now(timezone.utc)
    age = (now - value.astimezone(timezone.utc)).days
    if age < -1:
        return 35
    if age > 365:
        return 35
    if age > 120:
        return 22
    if age > 45:
        return 8
    return 0


def rank(title, text, source, published=None, now=None):
    """Return transparent collection triage, never the human editorial score."""
    heading = normalize(title)
    body = normalize((title or "") + " " + (text or "")[:12000])
    companies = _company_hits(heading, body)
    topics = [label for label, words in TOPICS.items() if any(contains(body, word) for word in words)]
    heading_topics = sum(any(contains(heading, word) for word in words) for words in TOPICS.values())

    signals = []
    outcome = bool(OUTCOME_RE.search(body))
    implementation = bool(IMPLEMENTATION_RE.search(body))
    pilot = bool(PILOT_RE.search(body))
    mechanism = bool(MECHANISM_RE.search(body))
    failure = bool(FAILURE_RE.search(body))
    standard = bool(STANDARD_RE.search(body))
    platform_shift = bool(PLATFORM_SHIFT_RE.search(body))
    if implementation:
        signals.append("Live or scaled implementation")
    elif pilot:
        signals.append("Pilot or test")
    if outcome:
        signals.append("Quantified or business outcome")
    if mechanism:
        signals.append("Concrete mechanism")
    if failure:
        signals.append("Failure or counter-evidence")
    if standard:
        signals.append("Rule, standard or measurement framework")
    if platform_shift:
        signals.append("Strategic platform shift")

    points = 10 * min(len(topics), 3) + 6 * min(heading_topics, 3)
    points += 12 if companies else 0
    points += 14 if outcome else 0
    points += 12 if implementation else (7 if pilot else 0)
    points += 10 if mechanism else 0
    points += 16 if failure else 0
    points += 16 if standard else 0
    points += 10 if platform_shift else 0
    if failure and FAILURE_RE.search(heading):
        points += 8
    if re.search(r"\b(?:case study|how\b|results?|implemented|builds?|uses?|scales?|measurement)\b", heading):
        points += 8

    if source.get("kind") in ("brand", "platform", "case_library", "standards", "regulator"):
        points += 4
    if GENERIC_RE.search(heading) and not (outcome or failure or standard):
        points -= 22
    if PARTNERSHIP_RE.search(heading) and not (outcome or implementation):
        points -= 16
    if CORPORATE_RE.search(heading):
        points -= 30
    points -= _freshness_penalty(published, now)
    points = max(0, min(100, points))

    beats = []
    source_beats = source.get("beats", [])
    if any(c in FMCG_COMPANIES for c in companies) or ("fmcg" in source_beats and topics):
        beats.append("FMCG")
    if any(c in ENTERPRISE_COMPANIES for c in companies) or ("enterprise" in source_beats and topics):
        beats.append("Enterprise")
    if "Connected consumer journey" in topics or ("journey" in source_beats and len(topics) >= 2):
        beats.append("Connected journey")
    if "Adtech and media infrastructure" in topics or "adtech" in source_beats:
        beats.append("Adtech")
    if "Regulation and standards" in topics or "regulation" in source_beats:
        beats.append("Regulation")

    kind = source.get("kind")
    if kind in ("brand", "platform", "case_library"):
        evidence = "Vendor/brand claim — verify outcome"
    elif kind in ("standards", "regulator"):
        evidence = "Primary rule or standards source"
    else:
        evidence = "Unreviewed reporting"
    if "sponsored" in body[:1600] or "partner content" in body[:1600]:
        evidence = "Sponsored content — verify claims"
    reason = "; ".join(signals) if signals else "Topic match only — verify mechanism, outcome and implication"
    return {
        "priority": points,
        "tags": topics,
        "companies": companies,
        "beats": beats,
        "evidence": evidence,
        "reason": reason,
        "signals": signals,
    }
