from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from typing import List, Optional
import json
import io
import email as pyemail
import re
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from models import (
    ProcessRequest, ProcessResponse,
    ExtractedOpportunity,
    RankedOpportunity, DiscardedOpportunity, FailedOpportunity,
    StudentProfile,
    AnalyticsResponse, ProcessWithAnalyticsResponse,
    HistoricalTrendsResponse,
)
from llm_client import extract_opportunity
from engine import (
    check_hard_disqualifiers,
    score_opportunity,
    generate_checklist,
    get_urgency_badge,
    normalize_date,
)
from analytics import OpportunityAnalytics, HistoricalAnalytics, CorpusStatistics

# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Opportunity Inbox Copilot",
    description="SOFTEC 2026 AI Hackathon – Email parsing + deterministic ranking",
    version="1.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Split text into multiple emails using --- or Subject: patterns
# ─────────────────────────────────────────────────────────────────────────────

def split_into_emails(text: str, source_name: str = "uploaded-file") -> List[str]:
    """
    Generic splitter that works for both pasted text and file uploads.
    Handles --- separators and Subject: headers.
    """
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Method 1: Split on --- separators (with optional whitespace)
    # This handles both "---" and "----------" style separators
    separator_pattern = r'\n\s*[-]{3,}\s*\n'
    raw_blocks = re.split(separator_pattern, text)
    
    # Clean and filter blocks
    blocks = []
    for block in raw_blocks:
        block = block.strip()
        # Must have substantial content with opportunity indicators
        if len(block) > 50 and ('Subject:' in block or 'From:' in block or 'Deadline:' in block or 'Eligibility:' in block):
            blocks.append(block)
    
    # If we found multiple valid blocks, format them
    if len(blocks) >= 2:
        formatted = []
        for i, block in enumerate(blocks):
            # Ensure block has Subject header for LLM parsing
            if not re.search(r'^Subject:', block, re.MULTILINE):
                # Try to extract subject from content, or generate one
                subject_match = re.search(r'\nSubject:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
                from_match = re.search(r'\nFrom:\s*(.+?)(?:\n|$)', block, re.IGNORECASE)
                
                subject = subject_match.group(1).strip() if subject_match else f"Opportunity {i+1} from {source_name}"
                from_field = from_match.group(1).strip() if from_match else source_name
                
                block = f"Subject: {subject}\nFrom: {from_field}\n\n{block}"
            
            formatted.append(block)
        
        return formatted
    
    # Method 2: Split on Subject: headers if --- didn't work
    subject_positions = [m.start() for m in re.finditer(r'\nSubject:', text)]
    if len(subject_positions) >= 2:
        blocks = []
        for i, pos in enumerate(subject_positions):
            end_pos = subject_positions[i+1] if i+1 < len(subject_positions) else len(text)
            block = text[pos:end_pos].strip()
            if len(block) > 50:
                blocks.append(block)
        
        if len(blocks) >= 2:
            return blocks
    
    # Fallback: single document
    return [f"Subject: Document from {source_name}\nFrom: {source_name}\n\n{text}"]

# ─────────────────────────────────────────────────────────────────────────────
# ROOT / HEALTH
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Opportunity Inbox Copilot API",
        "version": "1.2.0",
        "scoring": {
            "skill_alignment_max": 55,
            "urgency_max": 15,
            "type_match_max": 15,
            "location_max": 10,
            "financial_bonus_max": 5,
            "completeness_max": 5,
            "total_max": 105,
        },
        "endpoints": {
            "POST /process": "Process emails (JSON) against a student profile",
            "POST /process-files": "Process uploaded files + optional text paste",
            "GET  /sample-data": "Get 15 sample emails + demo profile for testing",
            "GET  /health": "Health check",
            "GET  /docs": "Swagger UI",
        },
    }

@app.get("/health")
def health():
    return {"status": "ok"}

# ─────────────────────────────────────────────────────────────────────────────
# SAMPLE DATA  –  15 diverse emails + demo student profile
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_EMAILS: List[str] = [
    # ── Genuine opportunities ────────────────────────────────────────────────
    """Subject: Remote Cloud Security Internship – Apply Now!
Hi there,
CloudSec Pakistan is offering a 2-month remote internship in Cloud Security.
Skills required: Python, AWS, Cloud Security, Linux.
Deadline: in 3 days. Minimum CGPA: 3.0.
Required documents: Resume, Transcript.
Apply at: https://cloudsec.pk/intern
Contact: hr@cloudsec.pk""",

    """Subject: National Cybersecurity Hackathon 2025
Dear Student,
You are invited to the National Cybersecurity Hackathon hosted by NCA Pakistan.
Open to teams of 1-3. All degrees welcome.
Location: Remote (Online).
Deadline: in 10 days.
Prize pool: PKR 500,000.
Registration: https://nca.gov.pk/hackathon
Contact: hackathon@nca.gov.pk""",

    """Subject: LUMS Merit Scholarship – Final Year Students
Dear Applicant,
LUMS is offering a full merit scholarship for exceptional final-year undergraduate students.
Required CGPA: 3.5+.
Open to: BSCS, BSEE, BSMath students only.
Deadline: April 30, 2025.
Required documents: Transcript, Two recommendation letters, Statement of Purpose.
Apply: https://lums.edu.pk/scholarship
Financial award: Full tuition + stipend. This IS a scholarship.""",

    """Subject: Google Summer of Code 2025 – Open Source Internship
Hello Developer,
Google Summer of Code (GSoC) is accepting applications from university students worldwide.
You will work on an open-source project with a mentor for 10 weeks.
Stipend: USD 1,500–3,300.
Deadline: in 30 days.
Skills preferred: Python, Machine Learning, Algorithms.
Apply at: https://summerofcode.withgoogle.com
Open to all degrees and all years.""",

    """Subject: AI Research Fellowship – Tokyo Institute of Technology
Dear Student,
Tokyo Tech is inviting applications for its AI Research Fellowship (6 months, on-site in Tokyo).
Minimum requirements: CGPA 3.5+, N5 Japanese language certification mandatory.
Deadline: in 60 days.
Required: Resume, Research proposal, Two recommendation letters, Language certificate.
Apply: https://titech.ac.jp/fellowship""",

    """Subject: Data Science Internship – Xord (Lahore)
Hi,
Xord is hiring a Data Science intern for a 3-month position at our Lahore office.
Requirements: Python, Pandas, ML basics.
CGPA requirement: 2.8 minimum.
Deadline: in 7 days.
Send your CV to: careers@xord.com""",

    """Subject: HEC Need-Based Scholarship 2025
Dear Student,
The Higher Education Commission (HEC) Pakistan is offering need-based scholarships 
to deserving undergraduate students.
Eligibility: Financial need, CGPA 2.5+, Pakistani citizen.
Award: Full tuition coverage.
Deadline: May 15, 2025.
Required documents: Income certificate, CNIC copy, Transcript, Application form.
Apply online: https://hec.gov.pk/scholarships
This is a scholarship and grant program.""",

    """Subject: Microsoft AI Skills Challenge – Win Certifications
Dear Tech Enthusiast,
Join Microsoft's AI Skills Challenge and earn free Azure AI certifications!
Open to everyone. No fees. No restrictions.
Complete learning paths online at your own pace.
Challenge period: Ends in 14 days.
Link: https://microsoft.com/ai-challenge""",

    """Subject: Devsinc Frontend Internship – React Developer Needed
Hi,
Devsinc is looking for a Frontend Intern with React.js skills.
Location: Lahore (On-site).
Duration: 2 months.
Deadline: in 5 days.
Stipend: PKR 15,000/month.
Required: Resume, GitHub profile.
Apply: https://devsinc.com/careers""",

    """Subject: PIEAS Research Grant for Final Year Projects
Dear Senior Student,
PIEAS is offering research grants for BSCS and BSEE final-year students 
working on AI or Cybersecurity projects.
Grant amount: PKR 100,000.
Must be in semester 7 or 8.
Graduation year restriction: 2026.
Deadline: in 21 days.
Required: Project proposal, Faculty endorsement letter.
Apply: research@pieas.edu.pk
This is a grant.""",

    # ── Non-opportunities (should be discarded) ──────────────────────────────
    """Subject: University Cafeteria New Menu – Try Our Special Biryani!
Hey everyone,
The university cafeteria is launching its new spring menu next Monday.
Come try our famous Dumpukht Biryani at a special introductory price.
Main campus, Block B canteen. Open 8am – 8pm.
Management""",

    """Subject: Lost: Black Backpack near CS Department
Hi,
I lost my black JanSport backpack near the CS department on Wednesday evening.
It has my laptop and notes inside. If found, please contact me at 0300-1234567.
Reward offered. Thank you.""",

    """Subject: Student Society Elections – Cast Your Vote Tomorrow!
Dear Students,
The annual FAST Student Society elections will be held tomorrow, 18th April.
Please come and vote for your class representatives.
Voting booths open 9am–3pm in the main hall.
Electoral Committee""",

    """Subject: Library Fine Reminder
Dear Student,
This is a reminder that you have an outstanding library fine of PKR 450.
Please clear this fine at the library counter before the end of the month 
to avoid account suspension.
FAST-NU Library""",

    """Subject: Seminar on Blockchain Technology – This Friday
Dear Students,
The CS Department is hosting a guest lecture on Blockchain Technology 
by Mr. Ahmed Raza (Ex-Google) this Friday at 2pm in Auditorium B.
Attendance is voluntary. Refreshments will be served.
CS Department""",
]

DEMO_PROFILE = {
    "degree": "BSCS",
    "semester": 6,
    "cgpa": 3.4,
    "skills": ["Python", "Cloud Security", "React", "Machine Learning", "AWS"],
    "preferred_opportunity_types": ["internship", "hackathon", "scholarship"],
    "location_preference": "Lahore",
    "financial_need": True,
    "total_semesters": 8,
}

@app.get("/sample-data")
def get_sample_data():
    """Returns 15 diverse sample emails and a demo student profile for frontend testing."""
    return {
        "profile": DEMO_PROFILE,
        "emails": SAMPLE_EMAILS,
        "email_count": len(SAMPLE_EMAILS),
        "note": "Mix of real opportunities and non-opportunities for demo purposes.",
    }

# ─────────────────────────────────────────────────────────────────────────────
# CORE PIPELINE (shared by /process and /process-files)
# Includes all 8 fixes from improved engine.py
# ─────────────────────────────────────────────────────────────────────────────

def process_emails_logic(request: ProcessRequest) -> ProcessResponse:
    """
    Full deterministic pipeline with all improvements:
    - Fix #1: Rebalanced scoring (skill 55, urgency 15)
    - Fix #2: Skill synonyms + word-boundary matching
    - Fix #3: All disqualifier reasons collected
    - Fix #4: Expanded location keywords
    - Fix #5: Per-field completeness
    - Fix #6: Configurable total_semesters
    - Fix #7: Date confidence tracking
    - Fix #8: Priority-sorted checklist
    """
    if not request.emails:
        raise HTTPException(status_code=400, detail="No emails provided.")

    user_tz = getattr(request, 'user_timezone', 'UTC')
    ranked_list: List[RankedOpportunity] = []
    discarded_list: List[DiscardedOpportunity] = []
    failed_list: List[FailedOpportunity] = []

    for idx, email_text in enumerate(request.emails):
        snippet = email_text[:120].strip().replace("\n", " ") + "…"

        # ── Step 1: LLM extraction ────────────────────────────────────────
        extracted_data = extract_opportunity(email_text)

        if extracted_data is None:
            failed_list.append(FailedOpportunity(
                id=idx,
                reason="LLM failed to produce valid JSON after 3 attempts",
                snippet=snippet,
            ))
            continue

        # ── Step 2: Not an opportunity? ───────────────────────────────────
        if not extracted_data.get("is_opportunity", False):
            discarded_list.append(DiscardedOpportunity(
                id=idx,
                reason="Classified as non-opportunity by LLM",
                all_reasons=["Classified as non-opportunity by LLM"],
                snippet=snippet,
            ))
            continue

        # ── Step 3: Schema validation ─────────────────────────────────────
        try:
            opp = ExtractedOpportunity(**extracted_data)
        except (ValidationError, TypeError) as exc:
            failed_list.append(FailedOpportunity(
                id=idx,
                reason=f"Schema validation failed: {exc}",
                snippet=snippet,
            ))
            continue

        # ── Step 4: Hard disqualifiers ────────────────────────────────────
        # Fix #3: Returns (bool, List[str]) — all reasons, not just first
        is_disqualified, disq_reasons = check_hard_disqualifiers(request.profile, opp)
        if is_disqualified:
            primary = disq_reasons[0] if disq_reasons else "Unknown disqualification"
            discarded_list.append(DiscardedOpportunity(
                id=idx,
                reason=f"INELIGIBLE — {primary}",
                all_reasons=[f"INELIGIBLE — {r}" for r in disq_reasons],
                snippet=snippet,
            ))
            continue

        # ── Step 5: Deterministic scoring ────────────────────────────────
        # Uses: Fix #1 (rebalanced), Fix #2 (synonyms), Fix #4 (location), 
        #       Fix #5 (completeness), Fix #7 (date confidence)
        score_breakdown = score_opportunity(request.profile, opp, raw_email_body=email_text, user_timezone=user_tz)

        # ── Step 6: Checklist ─────────────────────────────────────────────
        # Fix #8: Priority-sorted (deadline → apply → docs)
        checklist = generate_checklist(opp)

        # ── Step 7: Urgency badge ─────────────────────────────────────────
        # Fix #7: normalize_date returns (iso, confidence)
        deadline_iso, _ = normalize_date(opp.deadline_raw, user_tz)
        urgency_badge = get_urgency_badge(score_breakdown.urgency.score)

        ranked_opp = RankedOpportunity(
            id=idx,
            title=opp.title or "Unknown Opportunity",
            org=opp.org or "Unknown Organization",
            type=opp.type or "other",
            deadline_iso=deadline_iso,
            urgency_badge=urgency_badge,
            score_breakdown=score_breakdown,
            checklist=checklist,
            link=opp.link,
            contact=opp.contact,
        )
        ranked_list.append(ranked_opp)

    # ── Sort by total score descending ────────────────────────────────────
    # Skill relevance is king (55 pts max) so total reflects fit, not urgency
    ranked_list.sort(key=lambda x: x.score_breakdown.total, reverse=True)

    return ProcessResponse(
        ranked_opportunities=ranked_list,
        discarded=discarded_list,
        failed=failed_list,
    )

# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 1:  POST /process  (original JSON, backward-compatible)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/process", response_model=ProcessResponse)
def process_emails(request: ProcessRequest):
    """
    Original JSON endpoint.
    Request body: {"profile": {...}, "emails": ["...", "---", "..."]}
    """
    return process_emails_logic(request)

# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 2:  POST /process-files  (multipart: files + optional text)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/process-files", response_model=ProcessResponse)
async def process_files(
    profile: str = Form(...),
    files: List[UploadFile] = File(default=[]),
    email_text: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
):
    """
    Multipart endpoint accepting:
      - profile: JSON string of StudentProfile
      - files:   .txt, .eml, .pdf  (multiple allowed)
      - email_text: raw pasted text with '---' separators (optional)

    All inputs flattened into single list, run through same improved pipeline.
    """
    # Parse profile JSON string into Pydantic model
    try:
        profile_dict = json.loads(profile)
        profile_obj = StudentProfile(**profile_dict)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid profile JSON: {exc}")

    all_emails: List[str] = []

    # ── Parse uploaded files ──────────────────────────────────────────────
    for upload in files:
        raw = await upload.read()

        if upload.filename and upload.filename.lower().endswith(".eml"):
            # Parse RFC-822 email format
            try:
                msg = pyemail.message_from_bytes(raw)
                header_block = (
                    f"Subject: {msg.get('Subject', '')}\n"
                    f"From: {msg.get('From', '')}\n"
                    f"Date: {msg.get('Date', '')}\n\n"
                )
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode("utf-8", errors="ignore")
                                break
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode("utf-8", errors="ignore")
                
                # Single .eml = single email (no splitting needed)
                all_emails.append(header_block + body)
                
            except Exception as exc:
                all_emails.append(
                    f"Subject: Parse Error\nFrom: system\n\nFailed to parse {upload.filename}: {exc}"
                )

        elif upload.filename and upload.filename.lower().endswith(".pdf"):
            # Extract text via PyPDF2, then use generic splitter
            try:
                import PyPDF2
                
                reader = PyPDF2.PdfReader(io.BytesIO(raw))
                full_text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                
                # Use generic splitter to handle --- separators
                pdf_emails = split_into_emails(full_text, upload.filename)
                all_emails.extend(pdf_emails)
                
            except Exception as exc:
                all_emails.append(
                    f"Subject: PDF Parse Error\n"
                    f"From: system\n\n"
                    f"Failed to parse {upload.filename}: {exc}"
                )

        else:
            # Treat everything else as plain text (.txt, .md, etc.)
            try:
                text = raw.decode("utf-8", errors="ignore")
                # Use generic splitter for .txt files too (they might have ---)
                txt_emails = split_into_emails(text, upload.filename)
                all_emails.extend(txt_emails)
                
            except Exception as exc:
                all_emails.append(
                    f"Subject: Read Error\nFrom: system\n\nFailed to read {upload.filename}: {exc}"
                )

    # ── Append pasted text (if any) ───────────────────────────────────────
    if email_text:
        # Use same splitter for consistency
        pasted_emails = split_into_emails(email_text, "pasted-text")
        all_emails.extend(pasted_emails)

    if not all_emails:
        raise HTTPException(status_code=400, detail="No emails or files provided.")

    # Build standard request and reuse core pipeline (with all 8 fixes)
    request = ProcessRequest(profile=profile_obj, emails=all_emails)
    result = process_emails_logic(request)

    # Save scan history to MySQL if user_id provided
    if user_id:
        try:
            from database.mysql_client import MySQLClient as _MC
            _mc = _MC()
            _mc.save_scan_history(user_id, {
                'ranked_count': len(result.ranked_opportunities),
                'discarded_count': len(result.discarded),
                'failed_count': len(result.failed),
                'results': {
                    'ranked': [r.dict() for r in result.ranked_opportunities[:5]],  # top 5 only
                }
            })
            _mc.close()
        except Exception as e:
            logger.warning(f"Failed to save scan history: {e}")

        # Push student + opportunities to Neo4j skill graph
        try:
            from database.neo4j_client import Neo4jClient as _Neo4j
            _neo = _Neo4j()

            # Student node — skills from profile
            _neo.create_student_node(user_id, profile_obj.skills)

            # Opportunity nodes — extract required skills from eligibility
            for opp in result.ranked_opportunities:
                opp_id = f"{user_id}_{opp.id}"
                # Use eligibility list from score breakdown reason as required skills
                required_skills = []
                skill_reason = opp.score_breakdown.skill_alignment.reason
                # Parse "Matched X/Y skills: skill1, skill2" format
                if "Matched" in skill_reason and ":" in skill_reason:
                    skills_part = skill_reason.split(":", 1)[-1].strip()
                    required_skills = [s.strip() for s in skills_part.split(",") if s.strip()]
                # Fallback: use profile skills that matched
                if not required_skills:
                    required_skills = profile_obj.skills[:3]

                _neo.create_opportunity_node(
                    opp_id=opp_id,
                    title=opp.title,
                    required_skills=required_skills,
                    org=opp.org,
                )

            _neo.close()
            logger.info(f"Neo4j: pushed student node + {len(result.ranked_opportunities)} opportunity nodes")
        except Exception as e:
            logger.warning(f"Neo4j push failed (non-critical): {e}")

    return result

# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 3:  POST /process-with-analytics  (returns scan results + analytics)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/process-with-analytics", response_model=ProcessWithAnalyticsResponse)
async def process_with_analytics(
    profile: str = Form(...),
    files: List[UploadFile] = File(default=[]),
    email_text: Optional[str] = Form(None),
):
    """
    Enhanced endpoint that returns both scan results and analytics.
    
    Accepts same inputs as /process-files:
      - profile: JSON string of StudentProfile
      - files:   .txt, .eml, .pdf  (multiple allowed)
      - email_text: raw pasted text with '---' separators (optional)
    
    Returns:
      - scan_results: Standard ProcessResponse with ranked/discarded/failed
      - analytics: Computed analytics including descriptive stats, distributions
    
    Requirements: 3.5
    """
    # Parse profile JSON string into Pydantic model
    try:
        profile_dict = json.loads(profile)
        profile_obj = StudentProfile(**profile_dict)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid profile JSON: {exc}")

    all_emails: List[str] = []

    # ── Parse uploaded files (same logic as /process-files) ──────────────
    for upload in files:
        raw = await upload.read()

        if upload.filename and upload.filename.lower().endswith(".eml"):
            try:
                msg = pyemail.message_from_bytes(raw)
                header_block = (
                    f"Subject: {msg.get('Subject', '')}\n"
                    f"From: {msg.get('From', '')}\n"
                    f"Date: {msg.get('Date', '')}\n\n"
                )
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode("utf-8", errors="ignore")
                                break
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode("utf-8", errors="ignore")
                
                all_emails.append(header_block + body)
                
            except Exception as exc:
                all_emails.append(
                    f"Subject: Parse Error\nFrom: system\n\nFailed to parse {upload.filename}: {exc}"
                )

        elif upload.filename and upload.filename.lower().endswith(".pdf"):
            try:
                import PyPDF2
                
                reader = PyPDF2.PdfReader(io.BytesIO(raw))
                full_text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                
                pdf_emails = split_into_emails(full_text, upload.filename)
                all_emails.extend(pdf_emails)
                
            except Exception as exc:
                all_emails.append(
                    f"Subject: PDF Parse Error\n"
                    f"From: system\n\n"
                    f"Failed to parse {upload.filename}: {exc}"
                )

        else:
            try:
                text = raw.decode("utf-8", errors="ignore")
                txt_emails = split_into_emails(text, upload.filename)
                all_emails.extend(txt_emails)
                
            except Exception as exc:
                all_emails.append(
                    f"Subject: Read Error\nFrom: system\n\nFailed to read {upload.filename}: {exc}"
                )

    # ── Append pasted text (if any) ───────────────────────────────────────
    if email_text:
        pasted_emails = split_into_emails(email_text, "pasted-text")
        all_emails.extend(pasted_emails)

    if not all_emails:
        raise HTTPException(status_code=400, detail="No emails or files provided.")

    # Build standard request and run through pipeline
    request = ProcessRequest(profile=profile_obj, emails=all_emails)
    scan_results = process_emails_logic(request)
    
    # ── Compute analytics ─────────────────────────────────────────────────
    if scan_results.ranked_opportunities:
        analytics_engine = OpportunityAnalytics(scan_results.ranked_opportunities)
        
        # Compute skill gaps
        skill_gaps = analytics_engine.compute_skill_gaps(profile_obj.skills)
        
        # Compute corpus statistics from email texts
        corpus_engine = CorpusStatistics(all_emails)
        corpus_stats = {
            'readability': corpus_engine.compute_readability_stats(),
            'keyword_density': corpus_engine.compute_keyword_density([
                'internship', 'scholarship', 'hackathon', 'deadline', 'apply',
                'eligibility', 'required', 'opportunity', 'program', 'award'
            ]),
            'top_terms': corpus_engine.get_top_terms(n=20)
        }
        
        # Extract keywords from opportunities
        keywords = corpus_engine.extract_keywords_from_opportunities(
            scan_results.ranked_opportunities, 
            n=30
        )
        
        analytics = AnalyticsResponse(
            descriptive_stats=analytics_engine.compute_descriptive_stats(),
            type_distribution=analytics_engine.get_type_distribution(),
            urgency_distribution=analytics_engine.get_urgency_distribution(),
            skill_gaps=skill_gaps,
            corpus_stats=corpus_stats,
            keywords=keywords,
            opportunities=scan_results.ranked_opportunities
        )
    else:
        # Empty results - return zero analytics
        analytics = AnalyticsResponse(
            descriptive_stats={'mean': 0.0, 'std': 0.0, 'percentiles': {'25': 0.0, '50': 0.0, '75': 0.0, '90': 0.0}},
            type_distribution={},
            urgency_distribution={},
            skill_gaps=[],
            corpus_stats={},
            keywords=[],
            opportunities=[]
        )
    
    return ProcessWithAnalyticsResponse(
        scan_results=scan_results,
        analytics=analytics
    )

# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT 4:  GET /analytics/history  (returns historical trends)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/analytics/history", response_model=HistoricalTrendsResponse)
def get_analytics_history(days: int = 30):
    """
    Returns historical trend analysis from scan history.
    
    Query parameters:
      - days: Number of days of history to analyze (default 30)
    
    Returns:
      - total_scans: Number of scans in the period
      - date_range: Start and end dates
      - opportunity_trend: Time series of opportunity counts
      - week_over_week_change: Percentage change from previous week
      - month_over_month_change: Percentage change from previous month
      - linear_regression: Trend line parameters
    
    Requirements: 5.4, 5.6
    """
    history_analytics = HistoricalAnalytics()
    
    # Load history
    df = history_analytics.load_history(days=days)
    
    if df.empty or len(df) < 2:
        # Insufficient data
        return HistoricalTrendsResponse(
            total_scans=len(df),
            date_range={'start': None, 'end': None},
            opportunity_trend=[],
            week_over_week_change=0.0,
            month_over_month_change=0.0,
            linear_regression={
                'slope': 0.0,
                'intercept': 0.0,
                'r_squared': 0.0,
                'insufficient_data': True
            }
        )
    
    # Compute trends
    trends = history_analytics.compute_trends()
    week_change = history_analytics.get_week_over_week_change()
    
    # Build opportunity trend time series
    df['timestamp_dt'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp_dt')
    
    opportunity_trend = []
    for _, row in df.iterrows():
        opportunity_trend.append({
            'date': row['timestamp'],
            'count': int(row.get('ranked_count', 0))
        })
    
    # Calculate month-over-month change (if we have enough data)
    month_change = 0.0
    if len(df) >= 2:
        # Simple approximation: compare first half vs second half
        midpoint = len(df) // 2
        first_half_avg = df.iloc[:midpoint]['ranked_count'].mean()
        second_half_avg = df.iloc[midpoint:]['ranked_count'].mean()
        
        if first_half_avg > 0:
            month_change = ((second_half_avg - first_half_avg) / first_half_avg) * 100
    
    return HistoricalTrendsResponse(
        total_scans=len(df),
        date_range={
            'start': df['timestamp'].iloc[0],
            'end': df['timestamp'].iloc[-1]
        },
        opportunity_trend=opportunity_trend,
        week_over_week_change=week_change,
        month_over_month_change=month_change,
        linear_regression=trends
    )

# ─────────────────────────────────────────────────────────────────────────────
# PROFILE PERSISTENCE ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

from database.mysql_client import MySQLClient
from models import ProfileSaveRequest, ProfileResponse

# ─────────────────────────────────────────────────────────────────────────────
# AUTH ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel as _BaseModel

class SignupRequest(_BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(_BaseModel):
    email: str
    password: str

class AuthResponse(_BaseModel):
    user_id: str
    email: str
    name: str
    status: str

@app.post("/auth/signup", response_model=AuthResponse)
def signup(request: SignupRequest):
    """Register a new user — stores hashed password in MySQL"""
    try:
        client = MySQLClient()
        result = client.signup(request.name, request.email, request.password)
        client.close()
        return AuthResponse(
            user_id=result["user_id"],
            email=result["email"],
            name=result["name"],
            status="created"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")

@app.post("/auth/login", response_model=AuthResponse)
def login(request: LoginRequest):
    """Authenticate user — verifies bcrypt password hash"""
    try:
        client = MySQLClient()
        result = client.login(request.email, request.password)
        client.close()
        return AuthResponse(
            user_id=result["user_id"],
            email=result["email"],
            name=result["name"],
            status="authenticated"
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.post("/profile", response_model=ProfileResponse)
def save_profile(request: ProfileSaveRequest):
    """Save or update user profile to MySQL database"""
    try:
        client = MySQLClient()
        
        # Convert profile to dict
        profile_data = request.profile.dict()
        
        # Save to database
        result = client.save_profile(request.user_id, profile_data)
        client.close()
        
        return ProfileResponse(
            user_id=request.user_id,
            profile=request.profile,
            status="saved"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save profile: {str(e)}")


@app.get("/profile/{user_id}", response_model=ProfileResponse)
def get_profile(user_id: str):
    """Retrieve user profile from MySQL database"""
    try:
        client = MySQLClient()
        
        # Get profile from database
        profile_data = client.get_profile(user_id)
        client.close()
        
        if not profile_data:
            return ProfileResponse(
                user_id=user_id,
                profile=None,
                status="not_found"
            )
        
        # Convert to StudentProfile model
        profile = StudentProfile(
            degree=profile_data['degree'],
            semester=profile_data['semester'],
            cgpa=profile_data['cgpa'],
            skills=profile_data['skills'],
            preferred_opportunity_types=profile_data['preferred_opportunity_types'],
            location_preference=profile_data['location_preference'],
            financial_need=profile_data['financial_need'],
            total_semesters=profile_data['total_semesters']
        )
        
        return ProfileResponse(
            user_id=user_id,
            profile=profile,
            status="found"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve profile: {str(e)}")

# ─────────────────────────────────────────────────────────────────────────────
# BOOKMARK ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

from models import BookmarkRequest, BookmarkResponse

@app.post("/bookmarks", response_model=BookmarkResponse)
def save_bookmark(request: BookmarkRequest):
    """Save an opportunity as a bookmark"""
    try:
        client = MySQLClient()
        
        # Save bookmark to database
        result = client.save_bookmark(request.user_id, request.opportunity_data)
        client.close()
        
        return BookmarkResponse(
            bookmark_id=result['bookmark_id'],
            status="saved"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save bookmark: {str(e)}")


@app.delete("/bookmarks/{user_id}/{opportunity_id}")
def remove_bookmark(user_id: str, opportunity_id: str):
    """Remove a bookmark"""
    try:
        client = MySQLClient()
        
        # Remove bookmark from database
        success = client.remove_bookmark(user_id, opportunity_id)
        client.close()
        
        if success:
            return {"status": "removed", "user_id": user_id, "opportunity_id": opportunity_id}
        else:
            raise HTTPException(status_code=404, detail="Bookmark not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove bookmark: {str(e)}")


@app.get("/bookmarks/{user_id}")
def get_bookmarks(user_id: str):
    """Get all bookmarked opportunities for a user"""
    try:
        client = MySQLClient()
        
        # Get bookmarks from database
        bookmarks = client.get_bookmarks(user_id)
        client.close()
        
        return {
            "user_id": user_id,
            "bookmarks": bookmarks,
            "count": len(bookmarks)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve bookmarks: {str(e)}")

# ─────────────────────────────────────────────────────────────────────────────
# EMAIL SCANNING ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

from models import ScanEmailRequest, InboxScanRequest, InboxScanResponse
from email_scanner import GmailScanner, OutlookScanner, EmailProcessor
from imap_config import get_setup_instructions, list_supported_providers
from inbox_extractor import extract_and_categorize_emails

@app.post("/scan-gmail", response_model=InboxScanResponse)
def scan_gmail(request: InboxScanRequest):
    """
    Scan email inbox and extract categorized emails (PROFILE-INDEPENDENT MODE).
    
    This endpoint does NOT use profile-based filtering or scoring.
    It extracts and categorizes all important emails from the user's inbox:
    - Opportunities (internships, scholarships, hackathons)
    - Meetings
    - Interviews
    - Deadlines
    - Grants
    
    Supports ALL IMAP-compatible providers:
    - Gmail, Yahoo, Outlook/Hotmail, iCloud, AOL, Zoho, ProtonMail, FastMail
    - Any custom IMAP server
    
    Accepts:
      - provider: Provider name (gmail, yahoo, outlook, icloud, aol, zoho, protonmail, fastmail)
      - credentials: Email and app password dictionary
      - max_emails: Maximum number of emails to fetch (default 100)
      - NO profile field (profile-independent mode)
    
    Returns:
      - InboxScanResponse with categorized emails
    
    Requirements: 9.4, 9.5, 11.5
    """
    try:
        # Initialize scanner (auto-detects IMAP server from email domain)
        logger.info(f"Initializing email scanner for provider '{request.provider}' with {request.max_emails} max emails")
        scanner = GmailScanner(request.credentials)
        
        # Authenticate
        logger.info(f"Authenticating with {request.provider}")
        scanner.authenticate()
        
        # Fetch emails (just raw email text, no profile processing)
        logger.info(f"Fetching up to {request.max_emails} emails")
        emails = scanner.fetch_emails_raw(max_results=request.max_emails)
        
        if not emails:
            logger.info(f"No emails extracted from {request.provider}")
            return InboxScanResponse(
                opportunities=[],
                meetings=[],
                interviews=[],
                deadlines=[],
                grants=[],
                other_important=[],
                discarded=[],
                failed=[],
                total_scanned=0
            )
        
        logger.info(f"Successfully extracted {len(emails)} emails, categorizing without profile filtering")
        
        # Extract and categorize (NO profile filtering)
        result = extract_and_categorize_emails(emails)
        
        logger.info(
            f"{request.provider.capitalize()} scan complete: {len(result.opportunities)} opportunities, "
            f"{len(result.meetings)} meetings, {len(result.interviews)} interviews, "
            f"{len(result.deadlines)} deadlines, {len(result.grants)} grants, "
            f"{len(result.discarded)} discarded, {len(result.failed)} failed"
        )

        # ── Persist to MySQL + Neo4j if user_id provided ──────────────────
        if request.user_id:
            # MySQL: save scan history
            try:
                from database.mysql_client import MySQLClient as _MC
                _mc = _MC()
                total_extracted = (len(result.opportunities) + len(result.meetings) +
                                   len(result.interviews) + len(result.deadlines) +
                                   len(result.grants) + len(result.other_important))
                _mc.save_scan_history(request.user_id, {
                    'ranked_count': len(result.opportunities),
                    'discarded_count': len(result.discarded),
                    'failed_count': len(result.failed),
                    'results': {
                        'source': 'inbox_scan',
                        'provider': request.provider,
                        'total_scanned': result.total_scanned,
                        'opportunities': [o.dict() for o in result.opportunities[:5]],
                    }
                })
                _mc.close()
                logger.info(f"MySQL: saved inbox scan history for user {request.user_id}")
            except Exception as e:
                logger.warning(f"MySQL inbox scan history save failed: {e}")

            # Neo4j: push opportunity nodes from inbox scan
            try:
                from database.neo4j_client import Neo4jClient as _Neo4j
                _neo = _Neo4j()
                for opp in result.opportunities:
                    opp_id = f"inbox_{request.user_id}_{opp.id}"
                    required_skills = [r.lower() for r in (opp.requirements or [])[:5]]
                    _neo.create_opportunity_node(
                        opp_id=opp_id,
                        title=opp.title,
                        required_skills=required_skills,
                        org=opp.org or '',
                    )
                _neo.close()
                logger.info(f"Neo4j: pushed {len(result.opportunities)} inbox opportunity nodes")
            except Exception as e:
                logger.warning(f"Neo4j inbox push failed (non-critical): {e}")

        return result
        
    except HTTPException:
        raise
        
    except ValueError as e:
        # Credential validation errors
        logger.error(f"{request.provider} credential validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid credentials: {str(e)}"
        )
        
    except Exception as e:
        # All other errors (authentication, API errors, etc.)
        logger.error(f"{request.provider} scan error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scan {request.provider}: {str(e)}"
        )

# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT:  POST /scan-outlook  (Outlook email scanning)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/scan-outlook", response_model=InboxScanResponse)
def scan_outlook(request: InboxScanRequest):
    """
    Scan Outlook inbox and extract categorized emails (PROFILE-INDEPENDENT MODE).
    
    This endpoint does NOT use profile-based filtering or scoring.
    It extracts and categorizes all important emails from the user's inbox:
    - Opportunities (internships, scholarships, hackathons)
    - Meetings
    - Interviews
    - Deadlines
    - Grants
    
    Accepts:
      - provider: 'outlook' (validated)
      - credentials: OAuth credentials dictionary
      - max_emails: Maximum number of emails to fetch (default 100)
      - NO profile field (profile-independent mode)
    
    Returns:
      - InboxScanResponse with categorized emails
    
    Requirements: 10.4, 10.5, 11.5
    """
    try:
        # Validate provider
        if request.provider.lower() != 'outlook':
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider '{request.provider}'. This endpoint only accepts 'outlook'."
            )
        
        # Initialize Outlook scanner
        logger.info(f"Initializing Outlook scanner for user with {request.max_emails} max emails")
        scanner = OutlookScanner(request.credentials)
        
        # Authenticate
        logger.info("Authenticating with Outlook")
        scanner.authenticate()
        
        # Fetch emails (just raw email text, no profile processing)
        logger.info(f"Fetching up to {request.max_emails} emails")
        emails = scanner.fetch_emails_raw(max_results=request.max_emails)
        
        if not emails:
            logger.info("No emails extracted from Outlook")
            return InboxScanResponse(
                opportunities=[],
                meetings=[],
                interviews=[],
                deadlines=[],
                grants=[],
                other_important=[],
                discarded=[],
                failed=[],
                total_scanned=0
            )
        
        logger.info(f"Successfully extracted {len(emails)} emails, categorizing without profile filtering")
        
        # Extract and categorize (NO profile filtering)
        result = extract_and_categorize_emails(emails)
        
        logger.info(
            f"Outlook scan complete: {len(result.opportunities)} opportunities, "
            f"{len(result.meetings)} meetings, {len(result.interviews)} interviews, "
            f"{len(result.deadlines)} deadlines, {len(result.grants)} grants, "
            f"{len(result.discarded)} discarded, {len(result.failed)} failed"
        )
        
        return result
        
    except HTTPException:
        raise
        
    except ValueError as e:
        # Credential validation errors
        logger.error(f"Outlook credential validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid credentials: {str(e)}"
        )
        
    except Exception as e:
        # All other errors (authentication, API errors, etc.)
        logger.error(f"Outlook scan error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scan Outlook: {str(e)}"
        )

# ─────────────────────────────────────────────────────────────────────────────
# CHECKLIST ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

from models import ChecklistUpdateRequest, ChecklistResponse

@app.post("/checklists", response_model=ChecklistResponse)
def save_checklist_item(request: ChecklistUpdateRequest):
    """Save or update a checklist item"""
    try:
        client = MySQLClient()
        
        # Save checklist item to database
        result = client.save_checklist_item(
            request.user_id,
            request.opportunity_id,
            request.task,
            request.done
        )
        client.close()
        
        return ChecklistResponse(
            checklist_id=result['checklist_id'],
            status="saved"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save checklist item: {str(e)}")


@app.get("/checklists/{user_id}/{opportunity_id}")
def get_checklist(user_id: str, opportunity_id: str):
    """Get checklist for an opportunity"""
    try:
        client = MySQLClient()
        
        # Get checklist from database
        checklist = client.get_checklist(user_id, opportunity_id)
        client.close()
        
        return {
            "user_id": user_id,
            "opportunity_id": opportunity_id,
            "checklist": checklist,
            "count": len(checklist)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve checklist: {str(e)}")

# ─────────────────────────────────────────────────────────────────────────────
# EMAIL CREDENTIALS ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

from models import ScanEmailRequest

@app.post("/email-credentials")
def save_email_credentials(request: dict):
    try:
        user_id = request.get('user_id')
        provider = request.get('provider')
        email_address = request.get('email_address')
        credentials = request.get('credentials')

        if not all([user_id, provider, email_address, credentials]):
            raise HTTPException(status_code=400, detail="Missing required fields: user_id, provider, email_address, credentials")

        client = MySQLClient()
        result = client.save_email_credentials(
            user_id=user_id,
            provider=provider.lower(),
            email_address=email_address,
            credentials=credentials
        )
        client.close()
        logger.info(f"Saved email credentials for user {user_id}, provider {provider}")
        return {"credential_id": result['credential_id'], "status": result['status'], "provider": provider, "email_address": email_address}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save email credentials: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save email credentials: {str(e)}")


@app.get("/email-credentials/{user_id}/{provider}")
def get_email_credentials(user_id: str, provider: str):
    try:
        client = MySQLClient()
        result = client.get_email_credentials(user_id, provider.lower())
        client.close()

        if not result:
            raise HTTPException(status_code=404, detail=f"No credentials found for user {user_id} and provider {provider}")

        return {
            "user_id": result['user_id'],
            "provider": result['provider'],
            "email_address": result['email_address'],
            "credentials": result['credentials'],
            "created_at": result['created_at'],
            "updated_at": result['updated_at'],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve email credentials: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve email credentials: {str(e)}")


@app.delete("/email-credentials/{user_id}/{provider}")
def delete_email_credentials(user_id: str, provider: str):
    try:
        client = MySQLClient()
        result = client.delete_email_credentials(user_id, provider.lower())
        client.close()
        return {"user_id": user_id, "provider": provider, "status": result['status']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete email credentials: {str(e)}")
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Failed to delete email credentials: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete email credentials: {str(e)}"
        )

# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT:  GET /email-providers  (List supported email providers)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/email-providers")
def get_email_providers():
    """
    Get list of supported email providers with their IMAP configurations.
    
    Returns:
        Dictionary of supported providers with setup information
    """
    try:
        providers = list_supported_providers()
        return {
            "supported_providers": providers,
            "total_count": len(providers)
        }
    except Exception as e:
        logger.error(f"Error listing email providers: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list email providers: {str(e)}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT:  POST /email-setup-instructions  (Get setup instructions for email)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/email-setup-instructions")
def get_email_setup_instructions(request: dict):
    """
    Get setup instructions for a specific email provider.
    
    Request body:
    {
        "email": "user@domain.com"
    }
    
    Returns:
        Setup instructions including:
        - Provider name
        - Setup URL
        - Step-by-step instructions
    """
    try:
        email = request.get('email')
        
        if not email:
            raise HTTPException(
                status_code=400,
                detail="Email address is required"
            )
        
        instructions = get_setup_instructions(email)
        
        return {
            "email": email,
            "provider": instructions['provider'],
            "setup_url": instructions['setup_url'],
            "instructions": instructions['instructions']
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting setup instructions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get setup instructions: {str(e)}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# GRAPH ENDPOINTS (Neo4j skill graph)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/graph/recommendations/{user_id}")
def get_skill_recommendations(user_id: str):
    """
    Query Neo4j for skill recommendations based on the student's known skills
    and the skills required by opportunities they've been matched with.
    Returns top 5 skills the student should learn next.
    """
    try:
        from database.neo4j_client import Neo4jClient as _Neo4j
        neo = _Neo4j()
        recommendations = neo.recommend_skills(user_id, n=5)
        skill_demand = neo.get_skill_demand()
        neo.close()
        return {
            "user_id": user_id,
            "recommended_skills": recommendations,
            "top_demanded_skills": skill_demand[:10],
        }
    except Exception as e:
        logger.warning(f"Neo4j recommendations failed: {e}")
        return {"user_id": user_id, "recommended_skills": [], "top_demanded_skills": []}


@app.get("/graph/skill-cooccurrence/{skill}")
def get_skill_cooccurrence(skill: str):
    """Return skills that frequently appear alongside the given skill in opportunities."""
    try:
        from database.neo4j_client import Neo4jClient as _Neo4j
        neo = _Neo4j()
        result = neo.get_skill_cooccurrence(skill)
        neo.close()
        return {"skill": skill, "related_skills": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




# ─────────────────────────────────────────────────────────────────────────────
# REPORT GENERATION ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel as _BaseModel
from typing import Any as _Any

class ReportRequest(_BaseModel):
    mode: str          # "copypaste" | "inbox"
    data: dict         # the scan result JSON

class ChartItem(_BaseModel):
    title: str
    caption: str
    image: str         # base64 PNG

class ReportResponse(_BaseModel):
    charts: List[ChartItem]
    generated_at: str
    mode: str

@app.post("/generate-report", response_model=ReportResponse)
def generate_report(request: ReportRequest):
    """
    Generate matplotlib charts for the Scan Report section.

    mode='copypaste' → 5 charts (score distribution, radar, skill gap, type pie, timeline)
    mode='inbox'     → 4 charts (category donut, sub-types, senders, urgency spread)

    Returns base64-encoded PNG images with captions.
    """
    try:
        from report_generator import generate_copypaste_report, generate_inbox_report
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Report generator not available: {e}")

    from datetime import datetime, timezone

    try:
        if request.mode == "copypaste":
            raw_charts = generate_copypaste_report(request.data)
        elif request.mode == "inbox":
            raw_charts = generate_inbox_report(request.data)
        else:
            raise HTTPException(status_code=400, detail="mode must be 'copypaste' or 'inbox'")

        charts = [
            ChartItem(
                title=c.get("title", ""),
                caption=c.get("caption", ""),
                image=c.get("image", ""),
            )
            for c in raw_charts
            if c and c.get("image")
        ]

        return ReportResponse(
            charts=charts,
            generated_at=datetime.now(timezone.utc).isoformat(),
            mode=request.mode,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)