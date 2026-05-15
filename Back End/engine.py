import re
import os
import json
import datetime
import numpy as np
import joblib
from dateutil.parser import parse as parse_date, ParserError
from models import StudentProfile, ExtractedOpportunity, ScoreBreakdown, ScoreDetail, ActionChecklist
from typing import List, Tuple, Optional

# ── Option 4: Match Scorer (loaded once at module level) ───────────────────
_ML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml")
_match_scorer = None
_match_feature_names = None
_match_reason_labels = {}

def _load_match_scorer():
    global _match_scorer, _match_feature_names, _match_reason_labels
    try:
        _match_scorer = joblib.load(os.path.join(_ML_DIR, "match_scorer.joblib"))
        meta = json.load(open(os.path.join(_ML_DIR, "feature_names.json")))
        _match_feature_names = meta["features"]
        _match_reason_labels = meta.get("reason_labels", {})
        print(f"[ml] Match scorer loaded ({len(_match_feature_names)} features)")
    except FileNotFoundError:
        print("[ml] Match scorer not found — using hardcoded scoring (run ml/train_matcher.py)")

_load_match_scorer()


def _extract_match_features(profile: StudentProfile, opp: ExtractedOpportunity,
                             matched_skills: list, deadline_iso: str | None) -> dict:
    """Extract numerical features for the match scorer."""
    # CGPA gap
    min_cgpa = opp.min_cgpa or 0.0
    cgpa_gap = profile.cgpa - min_cgpa

    # Skills overlap
    total_skills = len(profile.skills) if profile.skills else 1
    skills_overlap_count = len(matched_skills)
    skills_overlap_pct = skills_overlap_count / total_skills

    # Location match
    location_match = 0
    if opp.location:
        loc_lower = opp.location.lower()
        pref_lower = (profile.location_preference or "").lower()
        if loc_lower in ("remote", "online") or pref_lower in loc_lower or loc_lower in pref_lower:
            location_match = 1
    else:
        location_match = 1  # no restriction = match

    # Type preference match
    type_preference_match = 0
    if opp.type and profile.preferred_opportunity_types:
        opp_type_lower = opp.type.lower()
        if any(p.lower() in opp_type_lower or opp_type_lower in p.lower()
               for p in profile.preferred_opportunity_types):
            type_preference_match = 1

    # Graduation year match
    graduation_year_match = 1
    if opp.graduation_year_restriction:
        from datetime import datetime
        current_year = datetime.now().year
        semesters_left = profile.total_semesters - profile.semester
        est_grad_year = current_year + (semesters_left // 2)
        graduation_year_match = 1 if est_grad_year <= opp.graduation_year_restriction else 0

    # Financial need bonus
    financial_need = 1 if profile.financial_need else 0
    is_scholarship = 1 if opp.is_scholarship_or_grant else 0

    # Urgency score (exponential decay)
    urgency_score = 0.0
    if deadline_iso:
        try:
            from datetime import datetime, timezone
            deadline_dt = datetime.fromisoformat(deadline_iso.replace("Z", "+00:00"))
            now = datetime.now(deadline_dt.tzinfo) if deadline_dt.tzinfo else datetime.now()
            days_left = max(0, (deadline_dt - now).days)
            urgency_score = 1.0 / (1.0 + days_left / 30.0)
        except Exception:
            urgency_score = 0.1

    # Quality signal (composite — use skills_overlap_pct as proxy if not available)
    quality_signal = skills_overlap_pct

    # Interaction terms
    cgpa_x_skills = cgpa_gap * skills_overlap_pct
    financial_x_scholarship = financial_need * is_scholarship

    return {
        "cgpa_gap": cgpa_gap,
        "skills_overlap_pct": skills_overlap_pct,
        "location_match": location_match,
        "type_preference_match": type_preference_match,
        "graduation_year_match": graduation_year_match,
        "financial_need": financial_need,
        "is_scholarship": is_scholarship,
        "urgency_score": urgency_score,
        "quality_signal": quality_signal,
        "cgpa_x_skills": cgpa_x_skills,
        "financial_x_scholarship": financial_x_scholarship,
    }


def ml_score_opportunity(profile: StudentProfile, opp: ExtractedOpportunity,
                          matched_skills: list, deadline_iso: str | None) -> tuple[float | None, dict]:
    """
    Option 4: Returns (ml_score_0_to_1, top_reasons_dict).
    Returns (None, {}) if model not loaded — caller falls back to hardcoded scoring.
    """
    if _match_scorer is None or _match_feature_names is None:
        return None, {}

    features = _extract_match_features(profile, opp, matched_skills, deadline_iso)
    X = np.array([[features.get(f, 0.0) for f in _match_feature_names]])
    score = float(np.clip(_match_scorer.predict(X)[0], 0.0, 1.0))

    # Top 2 feature importances → human-readable reasons
    importances = dict(zip(_match_feature_names, _match_scorer.feature_importances_))
    top_features = sorted(importances.items(), key=lambda x: -x[1])[:2]
    top_reasons = {feat: _match_reason_labels.get(feat, feat) for feat, _ in top_features}

    return score, top_reasons

# ─────────────────────────────────────────────────────────────────────────────
# FIX #2 — SKILL SYNONYM MAP
# Covers the most common aliases in tech/CS/AI job postings.
# Keys and values are all lowercase.
# ─────────────────────────────────────────────────────────────────────────────

SKILL_ALIASES: dict[str, List[str]] = {
    "machine learning":          ["ml", "machine-learning"],
    "ml":                        ["machine learning", "machine-learning"],
    "artificial intelligence":   ["ai"],
    "ai":                        ["artificial intelligence"],
    "natural language processing": ["nlp"],
    "nlp":                       ["natural language processing"],
    "deep learning":             ["dl", "deep-learning"],
    "dl":                        ["deep learning", "deep-learning"],
    "javascript":                ["js"],
    "js":                        ["javascript"],
    "typescript":                ["ts"],
    "ts":                        ["typescript"],
    "react":                     ["reactjs", "react.js"],
    "reactjs":                   ["react", "react.js"],
    "node":                      ["nodejs", "node.js"],
    "nodejs":                    ["node", "node.js"],
    "python":                    ["py"],
    "py":                        ["python"],
    "cloud security":            ["infosec", "cloud sec", "cybersecurity", "cyber security"],
    "cybersecurity":             ["cloud security", "cyber security", "infosec", "information security"],
    "cyber security":            ["cybersecurity", "cloud security", "infosec"],
    "aws":                       ["amazon web services", "amazon aws"],
    "amazon web services":       ["aws"],
    "gcp":                       ["google cloud", "google cloud platform"],
    "google cloud":              ["gcp", "google cloud platform"],
    "azure":                     ["microsoft azure"],
    "microsoft azure":           ["azure"],
    "computer vision":           ["cv", "image recognition", "image processing"],
    "cv":                        ["computer vision"],
    "data science":              ["data analytics", "data analysis"],
    "linux":                     ["unix", "bash", "shell scripting"],
    "bash":                      ["linux", "shell", "shell scripting"],
    "sql":                       ["mysql", "postgresql", "postgres", "database"],
    "mysql":                     ["sql", "database"],
    "postgresql":                ["sql", "postgres", "database"],
    "devops":                    ["ci/cd", "cicd", "docker", "kubernetes"],
    "docker":                    ["containerization", "containers"],
    "kubernetes":                ["k8s", "container orchestration"],
}


def skill_in_text(skill: str, text: str) -> bool:
    """
    Fix #2 — word-boundary match + synonym expansion.
    Returns True if skill OR any of its aliases appears in text as a whole word.
    Both skill and text are lowercased once so matching is case-insensitive throughout.
    """
    skill_lower = skill.lower()
    text_lower  = text.lower()          # lowercase once — covers primary AND alias checks

    # Primary word-boundary match
    pattern = r'\b' + re.escape(skill_lower) + r'\b'
    if re.search(pattern, text_lower):
        return True

    # Alias expansion
    for alias in SKILL_ALIASES.get(skill_lower, []):
        alias_pattern = r'\b' + re.escape(alias) + r'\b'
        if re.search(alias_pattern, text_lower):
            return True

    return False


# ─────────────────────────────────────────────────────────────────────────────
# DATE NORMALIZATION
# Fix #7 — returns (iso_date, confidence) instead of just iso_date.
# confidence: "high" (relative strings / unambiguous absolute)
#             "medium" (ambiguous MM/DD vs DD/MM pattern)
#             "low"  (parse failed or no date)
# ─────────────────────────────────────────────────────────────────────────────

RELATIVE_PATTERNS = [
    (r"in\s+(\d+)\s+day",     lambda n: datetime.timedelta(days=int(n))),
    (r"in\s+(\d+)\s+week",    lambda n: datetime.timedelta(weeks=int(n))),
    (r"in\s+(\d+)\s+month",   lambda n: datetime.timedelta(days=int(n) * 30)),
    (r"within\s+(\d+)\s+day", lambda n: datetime.timedelta(days=int(n))),
    (r"(\d+)\s+days?\s+left", lambda n: datetime.timedelta(days=int(n))),
    (r"next\s+week",          lambda _: datetime.timedelta(weeks=1)),
]

# Pattern that could be MM/DD or DD/MM — ambiguous without locale context
_AMBIGUOUS_DATE_RE = re.compile(r'^\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}$')


def normalize_date(date_str: Optional[str], user_timezone: str = "UTC") -> Tuple[Optional[str], str]:
    """
    Returns (iso_date_string_or_None, confidence).
    confidence is "high", "medium", or "low".
    """
    if not date_str:
        return None, "low"

    date_str_lower = date_str.lower().strip()

    # Explicit relative keywords — unambiguous, high confidence
    if date_str_lower == "today":
        return datetime.date.today().isoformat(), "high"
    if date_str_lower == "tomorrow":
        return (datetime.date.today() + datetime.timedelta(days=1)).isoformat(), "high"

    for pattern, delta_fn in RELATIVE_PATTERNS:
        m = re.search(pattern, date_str_lower)
        if m:
            try:
                delta = delta_fn(m.group(1))
            except Exception:
                break
            return (datetime.date.today() + delta).isoformat(), "high"

    # Absolute date — check for ambiguity before parsing
    is_ambiguous = bool(_AMBIGUOUS_DATE_RE.match(date_str.strip()))

    try:
        dt = parse_date(date_str, fuzzy=True, dayfirst=False)
        confidence = "medium" if is_ambiguous else "high"
        return dt.date().isoformat(), confidence
    except (ParserError, OverflowError, ValueError):
        return None, "low"


# ─────────────────────────────────────────────────────────────────────────────
# HARD DISQUALIFIERS
# Fix #3 — collect ALL failure reasons instead of returning on the first one.
# Returns (is_disqualified: bool, reasons: List[str])
# ─────────────────────────────────────────────────────────────────────────────

def check_hard_disqualifiers(
    profile: StudentProfile,
    opp: ExtractedOpportunity,
) -> Tuple[bool, List[str]]:

    reasons: List[str] = []

    # 1. CGPA gate
    if opp.min_cgpa is not None and profile.cgpa < opp.min_cgpa:
        reasons.append(f"CGPA too low ({profile.cgpa} < required {opp.min_cgpa})")
        
    if getattr(opp, "max_cgpa", None) is not None and profile.cgpa > opp.max_cgpa:
        reasons.append(f"CGPA too high ({profile.cgpa} > max {opp.max_cgpa})")
        
    if getattr(opp, "requires_financial_need", False) and not profile.financial_need:
        reasons.append("Opportunity requires demonstrated financial need")

    # 2. Degree restriction
    if opp.degree_restrictions:
        profile_deg_lower = profile.degree.lower()
        matches = [
            d for d in opp.degree_restrictions
            if d.lower() in profile_deg_lower or profile_deg_lower in d.lower()
        ]
        if not matches:
            reasons.append(
                f"Degree '{profile.degree}' not eligible — "
                f"requires one of: {', '.join(opp.degree_restrictions)}"
            )

    # 3. Mandatory language certification
    if opp.mandatory_language:
        lang_lower = opp.mandatory_language.lower()
        has_lang = any(lang_lower in s.lower() for s in (profile.skills or []))
        if not has_lang:
            reasons.append(f"Missing mandatory language/cert: '{opp.mandatory_language}'")

    # 4. Graduation-year gate
    # Fix #6 — uses profile.total_semesters instead of hardcoded 8
    if opp.graduation_year_restriction is not None:
        current_year = datetime.datetime.now().year
        semesters_remaining = max(0, profile.total_semesters - profile.semester)
        semesters_per_year = getattr(profile, 'semesters_per_year', 2)
        years_remaining = semesters_remaining / max(1, semesters_per_year)
        estimated_grad_year = current_year + years_remaining
        if estimated_grad_year > opp.graduation_year_restriction:
            reasons.append(
                f"Graduation year mismatch "
                f"(estimated {int(estimated_grad_year)}, "
                f"required by {opp.graduation_year_restriction})"
            )

    return bool(reasons), reasons


# ─────────────────────────────────────────────────────────────────────────────
# URGENCY SCORE  (0–15)
# Fix #1 — max reduced from 30 → 15 to match type_match weight.
# Bands are rescaled proportionally.
# ─────────────────────────────────────────────────────────────────────────────

def calculate_urgency(deadline_iso: Optional[str]) -> Tuple[int, str]:
    if not deadline_iso:
        return 3, "Deadline unknown"

    try:
        deadline_date = datetime.date.fromisoformat(deadline_iso)
        today = datetime.date.today()
        diff = (deadline_date - today).days

        if diff < 0:
            return 0, f"Deadline already passed ({deadline_iso})"
            
        # Continuous decay formula: score drops from 15 to 1 as days increase to 60
        score = max(1, int(15 * (1 - min(diff, 60) / 60.0)))
        
        if diff <= 2:
            return score, f"CRITICAL — {diff} day(s) left"
        elif diff <= 7:
            return score, f"HIGH — {diff} days left"
        elif diff <= 14:
            return score, f"MEDIUM — {diff} days left"
        elif diff <= 30:
            return score, f"LOW — {diff} days left"
        else:
            return score, f"FUTURE — {diff} days left"
    except (ValueError, TypeError):
        return 3, "Could not calculate urgency from deadline"


# ─────────────────────────────────────────────────────────────────────────────
# LOCATION SCORE  (0–10)
# Fix #4 — expanded remote keyword set, international gets 2 pts baseline
#           instead of 0, unknown location gets 3 pts (was 0).
# ─────────────────────────────────────────────────────────────────────────────

_REMOTE_KEYWORDS = {
    "remote", "online", "virtual", "worldwide", "global",
    "anywhere", "work from home", "wfh", "hybrid",
}
_NATIONAL_KEYWORDS = {
    "pakistan", "national", "pk",
    "lahore", "karachi", "islamabad", "peshawar",
    "rawalpindi", "faisalabad", "multan", "quetta",
}


def calculate_location_score(
    opp_location: Optional[str],
    pref_location: str,
) -> Tuple[int, str]:

    if not opp_location:
        return 3, "Location not specified (partial credit)"

    loc_lower = opp_location.lower()
    pref_lower = pref_location.lower()

    # Remote / online — expanded keyword set
    if any(kw in loc_lower for kw in _REMOTE_KEYWORDS):
        return 10, f"Remote / online opportunity"

    # City-level exact match
    if pref_lower in loc_lower or loc_lower in pref_lower:
        return 8, f"City/region match: {opp_location}"

    # National (Pakistan-wide)
    if any(kw in loc_lower for kw in _NATIONAL_KEYWORDS):
        return 5, f"National opportunity: {opp_location}"

    # International — give 2 pts baseline (still accessible, not zero)
    return 2, f"International: {opp_location}"


# ─────────────────────────────────────────────────────────────────────────────
# COMPLETENESS SCORE  (0–5)
# Fix #5 — per-field scoring instead of binary 0/2/5 jump.
# deadline=2, link/contact=2, eligibility=1  →  max 5
# ─────────────────────────────────────────────────────────────────────────────

def calculate_completeness(opp: ExtractedOpportunity) -> Tuple[int, str]:
    score = 0
    present: List[str] = []
    missing: List[str] = []

    if opp.deadline_raw:
        score += 2
        present.append("deadline")
    else:
        missing.append("deadline")

    if opp.link or opp.contact:
        score += 2
        present.append("apply link/contact")
    else:
        missing.append("apply link/contact")

    if opp.eligibility:
        score += 1
        present.append("eligibility criteria")
    else:
        missing.append("eligibility criteria")

    if present:
        reason = f"Present: {', '.join(present)}"
        if missing:
            reason += f" | Missing: {', '.join(missing)}"
    else:
        reason = "No key fields found in email"

    return score, reason


# ─────────────────────────────────────────────────────────────────────────────
# SCORING ENGINE
# Fix #1 — skill_alignment max is now 55 pts (was 40).
#           urgency max is now 15 pts (was 30).
#           Total max stays at 105 pts (55+15+15+10+5+5=105).
# Fix #2 — uses skill_in_text() with word-boundary + synonym matching.
# Fix #4 — uses calculate_location_score() with expanded remote keywords.
# Fix #5 — uses calculate_completeness() with per-field scoring.
# Fix #7 — normalize_date() returns (iso, confidence); confidence stored in urgency ScoreDetail.
# ─────────────────────────────────────────────────────────────────────────────

def score_opportunity(
    profile: StudentProfile,
    opp: ExtractedOpportunity,
    raw_email_body: str = "",
    user_timezone: str = "UTC",
) -> ScoreBreakdown:

    # ── 1. Skill Alignment (0–55) ────────────────────────────────────────
    searchable_text = " ".join(filter(None, [
        opp.title or "",
        " ".join(opp.eligibility or []),
        raw_email_body,
    ])).lower()

    # Fix #2 — word-boundary + synonym matching
    matched_skills = [s for s in profile.skills if skill_in_text(s, searchable_text)]

    if profile.skills:
        match_ratio = len(matched_skills) / len(profile.skills)
        skill_score = int(match_ratio * 55)
        # Floor: 5 pts minimum so a real opportunity never scores zero on skills
        if skill_score == 0:
            skill_score = 5
    else:
        skill_score = 5

    skill_reason = (
        f"Matched {len(matched_skills)}/{len(profile.skills)} skills: "
        f"{', '.join(matched_skills)}"
        if matched_skills
        else "No skill overlap found (including synonyms), base score applied"
    )

    # ── 2. Urgency (0–15) ────────────────────────────────────────────────
    # Fix #7 — normalize_date now returns (iso, confidence)
    deadline_iso, date_confidence = normalize_date(opp.deadline_raw, user_timezone)
    urg_score, urg_reason = calculate_urgency(deadline_iso)

    # Append a note to the reason when date parsing was ambiguous
    if date_confidence == "medium":
        urg_reason += " (date format ambiguous — MM/DD vs DD/MM uncertain)"
    elif date_confidence == "low" and opp.deadline_raw:
        urg_reason += f" (could not parse: '{opp.deadline_raw}')"

    # ── 3. Opportunity-type match (0–15) ─────────────────────────────────
    type_score = 0
    type_reason = "No preferred type match"
    if opp.type:
        opp_type_lower = opp.type.lower()
        exact = any(p.lower() == opp_type_lower for p in profile.preferred_opportunity_types)
        partial = any(
            p.lower() in opp_type_lower or opp_type_lower in p.lower()
            for p in profile.preferred_opportunity_types
        )
        if exact:
            type_score = 15
            type_reason = f"Exact type match: '{opp.type}'"
        elif partial:
            type_score = 8
            type_reason = f"Partial type match: '{opp.type}'"

    # ── 4. Location alignment (0–10) ─────────────────────────────────────
    # Fix #4 — delegated to calculate_location_score()
    loc_score, loc_reason = calculate_location_score(opp.location, profile.location_preference)

    # ── 5. Financial bonus (0–5) ──────────────────────────────────────────
    fin_score = 0
    fin_reason = "No financial bonus applicable"
    if profile.financial_need and opp.is_scholarship_or_grant:
        fin_score = 5
        fin_reason = "Scholarship/grant + student has financial need"

    # ── 6. Completeness (0–5) ─────────────────────────────────────────────
    # Fix #5 — per-field scoring
    comp_score, comp_reason = calculate_completeness(opp)

    total = skill_score + urg_score + type_score + loc_score + fin_score + comp_score

    # ── Option 4: ML match scorer augmentation ────────────────────────────
    # Get ML-predicted match score (0–1) and convert to a bonus on top of
    # the existing 0–105 scale. ML score replaces total if model is loaded,
    # otherwise falls back to the hardcoded total above.
    ml_score, ml_reasons = ml_score_opportunity(
        profile, opp, matched_skills,
        deadline_iso if 'deadline_iso' in dir() else None
    )
    if ml_score is not None:
        # Blend: 60% ML score (scaled to 105) + 40% rule-based total
        ml_scaled = ml_score * 105
        total = int(0.6 * ml_scaled + 0.4 * total)
        total = max(0, min(105, total))

    return ScoreBreakdown(
        skill_alignment=ScoreDetail(score=skill_score, reason=skill_reason),
        urgency=ScoreDetail(
            score=urg_score,
            reason=urg_reason,
            date_confidence=date_confidence,   # Fix #7
        ),
        type_match=ScoreDetail(score=type_score, reason=type_reason),
        location=ScoreDetail(score=loc_score, reason=loc_reason),
        financial_bonus=ScoreDetail(score=fin_score, reason=fin_reason),
        completeness=ScoreDetail(score=comp_score, reason=comp_reason),
        total=total,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CHECKLIST GENERATOR
# Fix #8 — items sorted by priority: deadline first, apply link second, docs last.
# ─────────────────────────────────────────────────────────────────────────────

def generate_checklist(opp: ExtractedOpportunity) -> List[ActionChecklist]:
    items: List[ActionChecklist] = []

    # Priority 1 — deadline is the constraint everything else depends on
    if opp.deadline_raw:
        items.append(ActionChecklist(
            task=f"Submit before deadline: {opp.deadline_raw}",
            priority=1,
        ))

    # Priority 2 — apply link / contact
    if opp.link:
        items.append(ActionChecklist(task=f"Apply at: {opp.link}", priority=2))
    elif opp.contact:
        items.append(ActionChecklist(task=f"Contact: {opp.contact}", priority=2))

    # Priority 3 — document preparation
    for doc in (opp.required_docs or []):
        items.append(ActionChecklist(task=f"Prepare: {doc}", priority=3))

    if not items:
        items.append(ActionChecklist(
            task="Review opportunity details and apply",
            priority=3,
        ))

    # Sort by priority ascending (1 first)
    items.sort(key=lambda x: x.priority)
    return items


# ─────────────────────────────────────────────────────────────────────────────
# URGENCY BADGE HELPER
# Rescaled to match new max of 15.
# ─────────────────────────────────────────────────────────────────────────────

def get_urgency_badge(urgency_score: int) -> str:
    if urgency_score >= 15:
        return "CRITICAL"
    elif urgency_score >= 12:
        return "HIGH"
    elif urgency_score >= 8:
        return "MEDIUM"
    else:
        return "LOW"