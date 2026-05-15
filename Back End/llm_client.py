import json
import re
import os
import scipy.sparse
import joblib
import numpy as np
from dotenv import load_dotenv
from cerebras.cloud.sdk import Cerebras

# Load environment variables from the .env file
load_dotenv()

# Grab the key securely from the environment
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
if not CEREBRAS_API_KEY:
    raise ValueError("CEREBRAS_API_KEY is missing from the .env file!")

client = Cerebras(api_key=CEREBRAS_API_KEY)
MODEL_NAME = "llama3.1-8b"

# ── Option 2: Pre-classifier (loaded once at module level) ─────────────────
_ML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml")
_classifier = None
_text_vec = None
_threshold = 0.92  # fallback if model not trained yet

def _load_classifier():
    global _classifier, _text_vec, _threshold
    try:
        _classifier = joblib.load(os.path.join(_ML_DIR, "email_classifier.joblib"))
        _text_vec   = joblib.load(os.path.join(_ML_DIR, "vectorizer_text.joblib"))
        threshold_data = json.load(open(os.path.join(_ML_DIR, "optimal_threshold.json")))
        _threshold  = threshold_data.get("threshold", 0.92)
        print(f"[ml] Email pre-classifier loaded (threshold={_threshold:.4f})")
    except FileNotFoundError:
        print("[ml] Pre-classifier not found — all emails will go to LLM (run ml/train_classifier.py)")

_load_classifier()


def _should_skip_llm(email_text: str) -> bool:
    """
    Option 2 integration: returns True if the email is almost certainly
    not an opportunity, so the LLM call can be skipped entirely.
    Uses char_length + TF-IDF bigrams.
    """
    if _classifier is None or _text_vec is None:
        return False  # no model — don't skip anything

    char_len = len(email_text)
    X_text = _text_vec.transform([email_text])
    X_numeric = scipy.sparse.csr_matrix(np.array([[char_len]]))
    X = scipy.sparse.hstack([X_text, X_numeric])

    prob_not_opportunity = _classifier.predict_proba(X)[0][0]
    return bool(prob_not_opportunity >= _threshold)

# ─────────────────────────────────────────────────────────────────────────────
# PROMPT
# Temperature=0 for deterministic extraction.
# Combined classify + extract in one call (saves API round-trips).
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are an expert email parser for a student opportunity assistant.
Your job is to read ONE email and output a SINGLE valid JSON object.
DO NOT output any explanation, markdown, code fences, or extra text — ONLY the JSON.

CLASSIFICATION RULE:
Mark is_opportunity: true for ANY email that is actionable or time-sensitive for a student, including:
- Job offers, job alerts, hiring notices (full-time, part-time, contract, freelance)
- Internships, traineeships, apprenticeships
- Scholarships, grants, funding, financial aid
- Fellowships, research positions, lab openings
- Competitions, hackathons, challenges, coding contests
- Conferences, seminars, workshops, webinars, bootcamps (with registration or attendance)
- Meetings, interviews, screening calls (with a date/time)
- Deadlines, reminders, last-call notices for any of the above
- Admission offers, acceptance letters, enrollment notices
- Volunteer opportunities, community programs

Mark is_opportunity: false ONLY for clearly irrelevant emails:
- Cafeteria menus, lost & found, parking notices
- Birthday/farewell/party invitations with no professional relevance
- Generic newsletters with no specific actionable item
- Spam, promotional discount emails, marketing blasts
- Election/voting notices, library fines

When in doubt, mark is_opportunity: true. It is better to include a borderline email than to miss a real opportunity.

EXTRACTION SCHEMA (use exactly these keys):
{
  "is_opportunity": true,
  "type": "scholarship|internship|fellowship|competition|hackathon|grant|admission|job|part-time|volunteer|research|meeting|interview|workshop|webinar|seminar|conference|bootcamp|deadline|other",
  "title": "<short descriptive title>",
  "org": "<organization or institution name>",
  "deadline_raw": "<exact deadline/date/time string from the email, or null>",
  "event_date_raw": "<exact event/meeting/interview date-time string from the email, or null>",
  "eligibility": ["<criterion 1>", "<criterion 2>"],
  "required_docs": ["<document 1>", "<document 2>"],
  "link": "<application or registration URL, or null>",
  "contact": "<contact email/phone, or null>",
  "min_cgpa": <minimum CGPA as float, or null>,
  "mandatory_language": "<required language cert e.g. 'IELTS 6.5', or null>",
  "degree_restrictions": ["<e.g. BSCS>"],
  "graduation_year_restriction": <graduation year integer or null>,
  "location": "<Remote|Online|city|Country|null>",
  "is_scholarship_or_grant": <true if type is scholarship or grant, else false>,
  "confidence": <0.0 to 1.0 — your confidence this is a genuine actionable email>
}

IMPORTANT RULES:
- degree_restrictions: only fill if the email explicitly restricts to specific degrees. Leave [] if open to all.
- mandatory_language: only fill if a specific language cert is REQUIRED.
- deadline_raw: copy the EXACT deadline text. If it says "in 3 days", write "in 3 days".
- event_date_raw: for meetings/interviews/events, copy the exact date-time text (e.g. "Monday May 19 at 3:00 PM").
- confidence: 1.0 = clearly an opportunity, 0.5 = borderline, 0.1 = probably not but flagged.
- Output ONLY the JSON. No markdown. No prose.
"""

SIMPLIFIED_PROMPT = """\
You are an email classifier. Read the email and output ONLY a JSON object with these fields:
{"is_opportunity": true/false, "type": "job|internship|hackathon|meeting|interview|scholarship|other", "title": "short title", "org": "organization name", "confidence": 0.0-1.0}
Output ONLY the JSON. Nothing else.
"""

def _clean_json_response(raw: str) -> str:
    """Strip markdown fences and whitespace that LLMs sometimes add."""
    raw = raw.strip()
    # Remove ```json ... ``` or ``` ... ```
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _extract_json_from_text(text: str) -> str:
    """
    Last-resort JSON extractor.
    Finds the first { ... } block in the text even if the model added prose around it.
    Handles truncated JSON by attempting to close unclosed braces/brackets.
    """
    # Find the first opening brace
    start = text.find('{')
    if start == -1:
        return text
    
    # Walk forward tracking depth to find the matching closing brace
    depth = 0
    in_string = False
    escape_next = False
    
    for i, ch in enumerate(text[start:], start):
        if escape_next:
            escape_next = False
            continue
        if ch == '\\' and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    
    # JSON was truncated — return what we have and let the caller handle it
    return text[start:]


def _subject_line_hint(email_text: str) -> str:
    """
    Idea 4: Subject-line pre-filter.
    If the subject contains strong opportunity keywords, inject a hint into the prompt
    to bias the LLM toward is_opportunity: true.
    """
    # Extract subject line (first 300 chars is enough)
    header = email_text[:300].lower()
    
    strong_signals = [
        'intern', 'hiring', 'hackathon', 'fellowship', 'scholarship', 'apply',
        'opportunity', 'job', 'career', 'position', 'vacancy', 'opening',
        'interview', 'offer', 'invitation', 'register', 'enroll', 'competition',
        'contest', 'grant', 'funding', 'bootcamp', 'workshop', 'seminar',
        'webinar', 'conference', 'research', 'volunteer', 'program', 'admission',
        'codex', 'devops', 'engineer', 'developer', 'analyst', 'associate',
    ]
    
    matched = [kw for kw in strong_signals if kw in header]
    if matched:
        return f"\n\nHINT: The subject/header contains these keywords: {', '.join(matched[:5])}. This is likely an actionable email — lean toward is_opportunity: true unless it is clearly spam or irrelevant."
    return ""


def extract_opportunity(email_text: str) -> dict | None:
    """
    Send one email to Cerebras and return the parsed dict, or None on failure.
    - Option 2: Pre-classifier runs first — skips LLM if clearly not an opportunity
    - Full extraction attempted (3 tries with JSON repair)
    - On persistent parse failure, falls back to simplified prompt
    - Subject-line hint injected when strong keywords detected
    """
    # Option 2: fast local pre-classifier check
    if _should_skip_llm(email_text):
        return {"is_opportunity": False, "confidence": 0.05}

    hint = _subject_line_hint(email_text)
    
    base_user_msg = (
        f"Parse the following email and return ONLY a valid JSON object.{hint}\n\n"
        f"EMAIL:\n{email_text}"
    )
    user_msg = base_user_msg

    for attempt in range(3):  # 0, 1, 2
        try:
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_msg},
                ],
                model=MODEL_NAME,
                max_completion_tokens=1024,
                temperature=0.2,
                top_p=1,
                stream=False,
            )
            raw_content = response.choices[0].message.content
            cleaned = _clean_json_response(raw_content)
            # Try direct parse first, then regex extraction
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                extracted = _extract_json_from_text(raw_content)
                return json.loads(extracted)

        except json.JSONDecodeError as exc:
            if attempt < 2:
                user_msg = (
                    f"Your previous response was not valid JSON. "
                    f"Error: {exc}. "
                    f"Output ONLY the raw JSON object — no markdown, no explanation.\n\n"
                    f"EMAIL:\n{email_text}"
                )
            else:
                print(f"[llm_client] Full extraction failed after 3 attempts, trying simplified prompt...")
                return _extract_simplified(email_text)

        except Exception as exc:
            print(f"[llm_client] API error on attempt {attempt+1}: {exc}")
            if attempt == 2:
                return _extract_simplified(email_text)

    return None


def _extract_simplified(email_text: str) -> dict | None:
    """
    Simplified fallback extraction.
    Used when the full prompt causes JSON parse failures.
    Returns minimal fields — enough to classify and title the email.
    Never returns None for emails with strong opportunity signals in the subject.
    """
    truncated = email_text[:600]
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SIMPLIFIED_PROMPT},
                {"role": "user",   "content": f"EMAIL:\n{truncated}"},
            ],
            model=MODEL_NAME,
            max_completion_tokens=512,
            temperature=0.0,
            top_p=1,
            stream=False,
        )
        raw_content = response.choices[0].message.content
        # Try clean first, then regex extraction
        cleaned = _clean_json_response(raw_content)
        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError:
            extracted = _extract_json_from_text(raw_content)
            result = json.loads(extracted)
        
        # Fill in missing fields with safe defaults
        result.setdefault('deadline_raw', None)
        result.setdefault('event_date_raw', None)
        result.setdefault('eligibility', [])
        result.setdefault('required_docs', [])
        result.setdefault('link', None)
        result.setdefault('contact', None)
        result.setdefault('min_cgpa', None)
        result.setdefault('mandatory_language', None)
        result.setdefault('degree_restrictions', [])
        result.setdefault('graduation_year_restriction', None)
        result.setdefault('location', None)
        result.setdefault('is_scholarship_or_grant', False)
        result.setdefault('confidence', 0.5)
        return result

    except Exception as exc:
        print(f"[llm_client] Simplified extraction failed: {exc}")
        
        # Last resort: if subject line has strong signals, return a minimal stub
        # so the email at least shows up rather than being lost as a parse failure
        hint = _subject_line_hint(email_text)
        if hint:
            subject_match = re.search(r'subject[:\s]+(.+)', email_text[:300], re.IGNORECASE)
            title = subject_match.group(1).strip()[:80] if subject_match else 'Unknown Opportunity'
            print(f"[llm_client] Using subject-line stub for: {title}")
            return {
                'is_opportunity': True,
                'type': 'other',
                'title': title,
                'org': None,
                'deadline_raw': None,
                'event_date_raw': None,
                'eligibility': [],
                'required_docs': [],
                'link': None,
                'contact': None,
                'min_cgpa': None,
                'mandatory_language': None,
                'degree_restrictions': [],
                'graduation_year_restriction': None,
                'location': None,
                'is_scholarship_or_grant': False,
                'confidence': 0.45,
            }
        return None
