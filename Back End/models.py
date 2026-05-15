from pydantic import BaseModel, Field
from typing import List, Optional

class StudentProfile(BaseModel):
    degree: str
    semester: int
    cgpa: float
    skills: List[str]
    preferred_opportunity_types: List[str]
    location_preference: str
    financial_need: bool
    total_semesters: int = 8          # Fix #6 — configurable for Masters/diploma programs
    semesters_per_year: int = 2

class ProcessRequest(BaseModel):
    profile: StudentProfile
    emails: List[str]
    user_timezone: str = "UTC"

class ExtractedOpportunity(BaseModel):
    is_opportunity: bool
    type: Optional[str] = None
    title: Optional[str] = None
    org: Optional[str] = None
    deadline_raw: Optional[str] = None
    eligibility: Optional[List[str]] = []
    required_docs: Optional[List[str]] = []
    link: Optional[str] = None
    contact: Optional[str] = None
    min_cgpa: Optional[float] = None
    mandatory_language: Optional[str] = None
    degree_restrictions: Optional[List[str]] = []
    graduation_year_restriction: Optional[int] = None
    location: Optional[str] = None
    is_scholarship_or_grant: Optional[bool] = False
    max_cgpa: Optional[float] = None
    requires_financial_need: Optional[bool] = None

class ScoreDetail(BaseModel):
    score: int
    reason: str
    date_confidence: Optional[str] = None   # Fix #7 — "high" | "medium" | "low", only on urgency

class ScoreBreakdown(BaseModel):
    skill_alignment: ScoreDetail
    urgency: ScoreDetail
    type_match: ScoreDetail
    location: ScoreDetail
    financial_bonus: ScoreDetail
    completeness: ScoreDetail
    total: int
    # Fix #1 — max now 90 pts (skill 55 + urgency 15 + type 15 + loc 10 + fin 5 + comp 5 = 105 unchanged total but urgency capped at 15)

class ActionChecklist(BaseModel):
    task: str
    done: bool = False
    priority: int = 3                        # Fix #8 — 1=deadline, 2=apply, 3=document prep

class RankedOpportunity(BaseModel):
    id: int
    title: str
    org: str
    type: str
    deadline_iso: Optional[str] = None
    urgency_badge: str
    score_breakdown: ScoreBreakdown
    checklist: List[ActionChecklist]
    link: Optional[str] = None
    contact: Optional[str] = None

class DiscardedOpportunity(BaseModel):
    id: int
    reason: str                              # primary (first) reason — kept for backwards compat
    all_reasons: List[str] = []             # Fix #3 — all disqualifier reasons
    snippet: str

class FailedOpportunity(BaseModel):
    id: int
    reason: str
    snippet: str

class ProcessResponse(BaseModel):
    ranked_opportunities: List[RankedOpportunity]
    discarded: List[DiscardedOpportunity]
    failed: List[FailedOpportunity]

class AnalyticsResponse(BaseModel):
    descriptive_stats: dict
    type_distribution: dict
    urgency_distribution: dict
    skill_gaps: List[dict] = []
    corpus_stats: dict = {}
    keywords: List[dict] = []  # List of {keyword, frequency}
    opportunities: List[RankedOpportunity] = []  # For extracting scores

class ProcessWithAnalyticsResponse(BaseModel):
    scan_results: ProcessResponse
    analytics: AnalyticsResponse

class HistoricalTrendsResponse(BaseModel):
    total_scans: int
    date_range: dict  # start, end
    opportunity_trend: List[dict]  # [{date, count}, ...]
    week_over_week_change: float
    month_over_month_change: float
    linear_regression: dict  # slope, intercept, r_squared


# Profile persistence models
class ProfileSaveRequest(BaseModel):
    user_id: str
    profile: StudentProfile

class ProfileResponse(BaseModel):
    user_id: str
    profile: Optional[StudentProfile] = None
    status: str

# Bookmark models
class BookmarkRequest(BaseModel):
    user_id: str
    opportunity_id: str
    opportunity_data: dict

class BookmarkResponse(BaseModel):
    bookmark_id: str
    status: str

# Checklist models
class ChecklistUpdateRequest(BaseModel):
    user_id: str
    opportunity_id: str
    task: str
    done: bool

class ChecklistResponse(BaseModel):
    checklist_id: str
    status: str

# Email scanning models
class ScanEmailRequest(BaseModel):
    provider: str  # 'gmail' or 'outlook'
    credentials: dict  # OAuth credentials
    profile: StudentProfile
    max_emails: int = 100


# Profile-Independent Mode Models (for inbox scanning)
class CategorizedEmail(BaseModel):
    """Email extracted and categorized without profile-based filtering"""
    id: int
    category: str  # 'opportunity', 'meeting', 'interview', 'deadline', 'grant', 'other'
    title: str
    org: Optional[str] = None
    deadline_iso: Optional[str] = None
    deadline_proximity: Optional[str] = None  # 'urgent', 'soon', 'later'
    type: Optional[str] = None  # The specific LLM type (e.g., 'internship', 'job')
    
    # Type-specific metadata
    meeting_time: Optional[str] = None  # For meetings
    interview_time: Optional[str] = None  # For interviews
    grant_amount: Optional[str] = None  # For grants
    
    # Common metadata
    requirements: Optional[List[str]] = []
    required_docs: Optional[List[str]] = []
    link: Optional[str] = None
    contact: Optional[str] = None
    location: Optional[str] = None
    snippet: str  # First 150 chars of email

class InboxScanResponse(BaseModel):
    """Response for profile-independent inbox scanning"""
    opportunities: List[CategorizedEmail] = []
    meetings: List[CategorizedEmail] = []
    interviews: List[CategorizedEmail] = []
    deadlines: List[CategorizedEmail] = []
    grants: List[CategorizedEmail] = []
    other_important: List[CategorizedEmail] = []
    discarded: List[DiscardedOpportunity] = []  # Non-important emails
    failed: List[FailedOpportunity] = []
    total_scanned: int = 0

class InboxScanRequest(BaseModel):
    """Request for profile-independent inbox scanning"""
    provider: str  # 'gmail', 'outlook', or IMAP provider name
    credentials: dict  # OAuth tokens or app password
    max_emails: int = 100
    user_id: Optional[str] = None  # Optional — used to persist scan history
    # Note: No profile field - this is profile-independent mode
