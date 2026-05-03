from transformers import pipeline
import torch
import re

device = 0 if torch.cuda.is_available() else -1

classifier = pipeline(
    "zero-shot-classification",
    model="facebook/bart-large-mnli",
    device=device
)

CANDIDATE_LABELS = [
    "SH-7 share capital amendment form",
    "board resolution for capital change",
    "MGT-14 filing with ROC",
    "memorandum of association",
    "shareholder agreement or list",
]

CORPORATE_EVENT_LABELS = [
    "increase in authorised share capital",
    "allotment of equity shares",
    "reduction of capital",
]

DRAFT_KEYWORDS = ["draft", "proposed", "tentative", "not filed", "pending"]

DOC_TYPE_RULES = {
    "SH-7":             ["SH-7", "SH 7", "alteration of share capital", "alteration of authorised", "form sh"],
    "Board Resolution": ["RESOLVED THAT", "board resolution", "board of directors", "certified true copy"],
    "MGT-14":           ["MGT-14", "MGT 14", "filing of resolutions"],
    "MOA":              ["memorandum of association", "objects of the company", "main objects"],
    "Shareholders":     ["list of shareholders", "shareholder agreement", "register of members"],
}

CORPORATE_EVENT_RULES = {
    "increase in authorised capital": [
        r"increas.*authoris", r"authoris.*capital.*increas", r"alteration.*share capital", r"enhanced.*authoris"
    ],
    "allotment of equity shares": [
        r"allotment of.*shares", r"allot.*equity", r"shares.*allotted"
    ],
}


def rule_classify(text):
    text_lower = text.lower()
    doc_type, doc_conf = "Unknown", 0.0
    for label, keywords in DOC_TYPE_RULES.items():
        hits = sum(1 for kw in keywords if kw.lower() in text_lower)
        if hits > 0:
            score = min(0.5 + hits * 0.15, 0.99)
            if score > doc_conf:
                doc_conf, doc_type = score, label

    event, event_conf = "Unknown", 0.0
    for label, patterns in CORPORATE_EVENT_RULES.items():
        hits = sum(1 for p in patterns if re.search(p, text_lower))
        if hits > 0:
            score = min(0.5 + hits * 0.2, 0.99)
            if score > event_conf:
                event_conf, event = score, label

    return doc_type, round(doc_conf * 100, 1), event, round(event_conf * 100, 1)


def classify_document(text):
    doc_type, doc_conf, event, event_conf = rule_classify(text)

    if doc_conf < 50:
        doc_result = classifier(text[:2000], candidate_labels=CANDIDATE_LABELS)
        doc_type = doc_result["labels"][0]
        doc_conf = round(doc_result["scores"][0] * 100, 1)

    if event_conf < 50:
        event_result = classifier(text[:2000], candidate_labels=CORPORATE_EVENT_LABELS)
        event = event_result["labels"][0]
        event_conf = round(event_result["scores"][0] * 100, 1)

    return {
        "doc_type": doc_type,
        "filing_status": "Draft" if any(k in text.lower() for k in DRAFT_KEYWORDS) else "Official Filing",
        "corporate_event": event,
        "doc_type_confidence": doc_conf,
        "event_confidence": event_conf,
    }


def indian_format(n):
    try:
        n = int(str(n).replace(",", ""))
        s = str(n)
        if len(s) <= 3:
            return s
        last3 = s[-3:]
        rest = s[:-3]
        parts = []
        while len(rest) > 2:
            parts.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.append(rest)
        return ",".join(reversed(parts)) + "," + last3
    except:
        return str(n)


def format_capital(amount_raw, shares_raw=None, face_val="10"):
    try:
        amt = int(str(amount_raw).replace(",", ""))
        fv  = int(str(face_val).replace(",", ""))
        shares = int(str(shares_raw).replace(",", "")) if shares_raw else amt // fv
        return f"Rs. {indian_format(amt)} divided into {indian_format(shares)} Equity Shares of Rs. {fv} each"
    except:
        return str(amount_raw)


def extract_dates(text):
    return re.findall(
        r'(?:\d{1,2}\s+(?:January|February|March|April|May|June|July|'
        r'August|September|October|November|December)\s+\d{4}|'
        r'(?:January|February|March|April|May|June|July|August|September|'
        r'October|November|December)\s+\d{1,2},?\s+\d{4}|'
        r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
        text, re.IGNORECASE
    )


def extract_capital_table(text):
    # Company name
    company_name = "Not found"
    for pat in [
        r'Company[:\s]+([A-Za-z\s\(\)\.&]+(?:Private Limited|Pvt\.?\s*Ltd\.?))',  # ← NEW: matches "Company: Name Pvt Ltd"
        r'(?:Company Name|Name of Company)[:\s\|*]+([A-Za-z\s\(\)\.&]+(?:Private Limited|Pvt\.?\s*Ltd\.))',
        r'##\s+([A-Za-z\s\(\)\.&]+(?:Private Limited|Pvt\.?\s*Ltd\.))',
        r'\*\*Company[^:]*:\*\*\s*([A-Za-z\s\(\)\.&]+(?:Private Limited|Pvt\.?\s*Ltd\.))',
        r'([A-Za-z\s\(\)\.&]{5,}(?:Private Limited|Pvt\.?\s*Ltd\.))',
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            company_name = m.group(1).strip()
            break

    # Meeting date
    date_of_meeting = "-"
    for pat in [
        r'(?:Date of (?:Meeting|EGM|AGM|Filing)|held on)[:\s]+(\d{1,2}[thstndrd]*\s+\w+\s+\d{4})',
        r'(?:Date of (?:Meeting|EGM|AGM|Filing)|held on)[:\s]+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
        r'(?:Date of Filing)[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            date_of_meeting = m.group(1).strip()
            break
    if date_of_meeting == "-":
        dates = extract_dates(text)
        date_of_meeting = dates[0] if dates else "-"

    # Meeting type
    if re.search(r'\bAGM\b|Annual General Meeting', text, re.IGNORECASE):
        meeting_type = "AGM"
    elif re.search(r'\bEGM\b|Extraordinary General Meeting', text, re.IGNORECASE):
        meeting_type = "EGM"
    elif re.search(r'\bboard meeting\b', text, re.IGNORECASE):
        meeting_type = "Board"
    else:
        meeting_type = "-"

    # Source doc
    if re.search(r'\bSH-?7\b', text, re.IGNORECASE):
        source_doc = "SH-7"
    elif re.search(r'\bPAS-?3\b', text, re.IGNORECASE):
        source_doc = "PAS-3"
    elif re.search(r'\bMGT-?14\b', text, re.IGNORECASE):
        source_doc = "MGT-14"
    elif re.search(r'\bboard resolution\b', text, re.IGNORECASE):
        source_doc = "Board Resolution"
    else:
        source_doc = "-"

    rows = []

    # Pattern A: "Rs. X divided into Y Equity Shares of Rs. Z each"
    full_pat = re.compile(
        r'(?:Rs\.?|₹|INR)\s*([\d,]+)\s*(?:\([^)]*\))?\s*divided into\s*([\d,]+)\s*'
        r'(?:Equity\s*)?Shares?\s*of\s*(?:Rs\.?|₹)\s*([\d,]+)\s*each',
        re.IGNORECASE
    )
    full_matches = list(full_pat.finditer(text))

    # ── FIXED: one row per consecutive pair, each with its own date ──
    if len(full_matches) >= 2:
        all_dates = extract_dates(text)

        for i in range(len(full_matches) - 1):
            fm = full_matches[i]
            tm = full_matches[i + 1]

            # Find the date that appears just before this match in the text
            text_before = text[:fm.start()]
            local_dates = extract_dates(text_before)
            event_date = local_dates[-1] if local_dates else (
                all_dates[i] if i < len(all_dates) else date_of_meeting
            )

            rows.append({
                "date":       event_date,
                "from":       f"Rs. {fm.group(1)} divided into {fm.group(2)} Equity Shares of Rs. {fm.group(3)} each",
                "to":         f"Rs. {tm.group(1)} divided into {tm.group(2)} Equity Shares of Rs. {tm.group(3)} each",
                "agm_egm":    meeting_type,
                "source_doc": source_doc,
            })

    elif len(full_matches) == 1:
        tm = full_matches[0]
        rows.append({
            "date":       date_of_meeting,
            "from":       "-",
            "to":         f"Rs. {tm.group(1)} divided into {tm.group(2)} Equity Shares of Rs. {tm.group(3)} each",
            "agm_egm":    meeting_type,
            "source_doc": source_doc,
        })
    else:
        # Pattern B: inline "from Rs. X to Rs. Y"
        inline_pat = re.compile(
            r'from\s+(?:Rs\.?|₹|INR)?\s*([\d,]+)(?:\s*\([^)]*\))?\s+to\s+(?:Rs\.?|₹|INR)?\s*([\d,]+)',
            re.IGNORECASE
        )
        fv_m = re.search(r'(?:Rs\.?|₹)\s*([\d,]+)\s*(?:per share|each)', text, re.IGNORECASE)
        fv = fv_m.group(1) if fv_m else "10"
        for m in inline_pat.finditer(text):
            frm, to = m.group(1).replace(",", ""), m.group(2).replace(",", "")
            if int(to) > int(frm):
                rows.append({
                    "date":       date_of_meeting,
                    "from":       format_capital(frm, face_val=fv),
                    "to":         format_capital(to,  face_val=fv),
                    "agm_egm":    meeting_type,
                    "source_doc": source_doc,
                })
                break

    if not rows:
        rows.append({
            "date":       date_of_meeting,
            "from":       "[UNCONFIRMED]",
            "to":         "[UNCONFIRMED]",
            "agm_egm":    meeting_type,
            "source_doc": source_doc,
        })

    return {"company_name": company_name, "capital_table": rows}


def run_ai_pipeline(image_path, text_context):
    return {
        "result1_classification": classify_document(text_context),
        "result2_capital_table":  extract_capital_table(text_context),
    }