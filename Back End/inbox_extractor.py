"""
Profile-Independent Email Extraction and Categorization

This module handles inbox scanning mode where emails are extracted and categorized
WITHOUT profile-based filtering. Used for Gmail/Outlook/IMAP inbox scanning.

Key differences from profile-based mode:
- No CGPA/degree/skill filtering
- No profile-based scoring
- Focus on categorization and metadata extraction
- Assumes inbox emails are already relevant to the user
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import re
import logging

from models import CategorizedEmail, DiscardedOpportunity, FailedOpportunity, InboxScanResponse
from llm_client import extract_opportunity
from engine import normalize_date

logger = logging.getLogger(__name__)


def categorize_email_type(extracted_data: Dict) -> str:
    """
    Determine email category based on extracted data.
    Uses the LLM-returned type field first, then falls back to title keyword matching.
    """
    title = (extracted_data.get('title') or '').lower()
    email_type = (extracted_data.get('type') or '').lower()
    
    # Direct type mapping from LLM
    type_to_category = {
        'meeting': 'meeting',
        'interview': 'interview',
        'workshop': 'meeting',
        'webinar': 'meeting',
        'seminar': 'meeting',
        'conference': 'meeting',
        'bootcamp': 'opportunity',
        'job': 'opportunity',
        'part-time': 'opportunity',
        'volunteer': 'opportunity',
        'research': 'opportunity',
        'internship': 'opportunity',
        'scholarship': 'opportunity',
        'fellowship': 'opportunity',
        'hackathon': 'opportunity',
        'competition': 'opportunity',
        'grant': 'grant',
        'admission': 'opportunity',
        'deadline': 'deadline',
    }
    if email_type in type_to_category:
        return type_to_category[email_type]
    
    # Fallback: title keyword matching
    if any(kw in title for kw in ['meeting', 'seminar', 'workshop', 'webinar', 'session', 'lecture', 'conference call']):
        return 'meeting'
    if any(kw in title for kw in ['interview', 'screening', 'assessment', 'technical round', 'hr round']):
        return 'interview'
    if extracted_data.get('is_scholarship_or_grant') and 'grant' in title:
        return 'grant'
    if any(kw in title for kw in ['deadline', 'reminder', 'last date', 'final call', 'closing soon']):
        if not any(kw in title for kw in ['internship', 'scholarship', 'hackathon', 'job']):
            return 'deadline'
    if any(kw in title for kw in ['internship', 'scholarship', 'hackathon', 'competition', 'fellowship',
                                   'program', 'job', 'hiring', 'career', 'vacancy', 'opening',
                                   'bootcamp', 'research', 'volunteer', 'admission']):
        return 'opportunity'
    
    return 'other'


def calculate_deadline_proximity(deadline_iso: Optional[str]) -> Optional[str]:
    """
    Calculate how soon a deadline is approaching.
    
    Returns:
        'urgent' (< 3 days), 'soon' (3-14 days), 'later' (> 14 days), or None
    """
    if not deadline_iso:
        return None
    
    try:
        deadline = datetime.fromisoformat(deadline_iso.replace('Z', '+00:00'))
        now = datetime.now(deadline.tzinfo) if deadline.tzinfo else datetime.now()
        days_until = (deadline - now).days
        
        if days_until < 0:
            return 'expired'
        elif days_until <= 3:
            return 'urgent'
        elif days_until <= 14:
            return 'soon'
        else:
            return 'later'
    except (ValueError, AttributeError):
        return None


def extract_meeting_time(extracted_data: Dict, raw_email: str) -> Optional[str]:
    """Extract meeting time from email content"""
    # Look for common time patterns
    time_patterns = [
        r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))',
        r'(\d{1,2}\s*(?:AM|PM|am|pm))',
        r'at\s+(\d{1,2}:\d{2})',
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, raw_email, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def extract_grant_amount(extracted_data: Dict, raw_email: str) -> Optional[str]:
    """Extract grant/funding amount from email content"""
    # Look for currency patterns
    amount_patterns = [
        r'(PKR\s*[\d,]+)',
        r'(Rs\.?\s*[\d,]+)',
        r'(\$\s*[\d,]+)',
        r'(USD\s*[\d,]+)',
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, raw_email, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def is_important_email(extracted_data: Dict) -> bool:
    """
    Determine if an email is important enough to extract.
    
    Returns False only for clearly irrelevant emails.
    When in doubt, returns True (matches the LLM prompt philosophy).
    """
    if not extracted_data.get('is_opportunity', False):
        return False
    
    title = (extracted_data.get('title') or '').lower()
    
    # Only discard on very specific non-professional patterns
    # NOTE: 'event' alone is NOT a discard signal — hackathon invitations say "event"
    hard_discard = [
        'cafeteria', 'canteen', 'menu', 'food court',
        'lost and found', 'lost item', 'found item',
        'library fine', 'parking fine', 'parking notice',
        'birthday party', 'farewell party', 'sports day',
        'election notice', 'voting notice',
    ]
    
    if any(pattern in title for pattern in hard_discard):
        return False
    
    return True


# Confidence threshold for the "needs review" bucket (idea 6)
CONFIDENCE_THRESHOLD = 0.4


def extract_and_categorize_emails(emails: List[str]) -> InboxScanResponse:
    """
    Main function for profile-independent email extraction and categorization.
    
    This function:
    1. Extracts structured data from each email using LLM
    2. Categorizes emails by type (opportunity, meeting, interview, etc.)
    3. Extracts relevant metadata (deadlines, requirements, links)
    4. Does NOT apply profile-based filtering or scoring
    
    Args:
        emails: List of raw email text strings
    
    Returns:
        InboxScanResponse with categorized emails
    """
    response = InboxScanResponse(total_scanned=len(emails))
    
    for idx, email_text in enumerate(emails):
        snippet = email_text[:150].strip().replace("\n", " ") + "…"
        
        # Step 1: LLM extraction
        extracted_data = extract_opportunity(email_text)
        
        if extracted_data is None:
            response.failed.append(FailedOpportunity(
                id=idx,
                reason="LLM failed to extract data",
                snippet=snippet,
            ))
            continue
        
        # Step 2: Check if important
        if not is_important_email(extracted_data):
            # Build a descriptive discard reason
            snippet_lower = snippet.lower()
            if any(w in snippet_lower for w in ['unsubscribe', 'newsletter', 'promotional', 'offer', 'sale', 'discount']):
                reason = "Classified as non-opportunity — promotional/newsletter"
            elif any(w in snippet_lower for w in ['cafeteria', 'menu', 'food', 'canteen']):
                reason = "Classified as non-opportunity — campus notice"
            elif any(w in snippet_lower for w in ['lost', 'found', 'missing']):
                reason = "Classified as non-opportunity — lost & found"
            elif any(w in snippet_lower for w in ['birthday', 'farewell', 'party', 'sports day']):
                reason = "Classified as non-opportunity — social event"
            elif any(w in snippet_lower for w in ['vote', 'election', 'poll']):
                reason = "Classified as non-opportunity — election/vote"
            else:
                reason = "Classified as non-opportunity by LLM"
            
            response.discarded.append(DiscardedOpportunity(
                id=idx,
                reason=reason,
                all_reasons=[reason],
                snippet=snippet,
            ))
            continue
        
        # Idea 6: Low-confidence emails go to a "needs review" bucket in discarded
        confidence = extracted_data.get('confidence', 1.0)
        if confidence < CONFIDENCE_THRESHOLD:
            reason = f"Low confidence ({confidence:.0%}) — may need manual review"
            response.discarded.append(DiscardedOpportunity(
                id=idx,
                reason=reason,
                all_reasons=[reason],
                snippet=snippet,
            ))
            continue
        
        # Step 3: Categorize
        category = categorize_email_type(extracted_data)
        
        # Step 4: Extract metadata
        # Use event_date_raw for meetings/interviews, deadline_raw for opportunities
        date_raw = extracted_data.get('event_date_raw') or extracted_data.get('deadline_raw')
        deadline_iso, _ = normalize_date(extracted_data.get('deadline_raw'))
        event_date_iso, _ = normalize_date(date_raw) if date_raw != extracted_data.get('deadline_raw') else (deadline_iso, None)
        deadline_proximity = calculate_deadline_proximity(deadline_iso or event_date_iso)
        
        # Type-specific extraction
        meeting_time = (
            extracted_data.get('event_date_raw') or
            extract_meeting_time(extracted_data, email_text)
        ) if category in ('meeting', 'interview') else None
        interview_time = meeting_time if category == 'interview' else None
        grant_amount = extract_grant_amount(extracted_data, email_text) if category == 'grant' else None
        
        # Step 5: Create categorized email
        categorized = CategorizedEmail(
            id=idx,
            category=category,
            type=extracted_data.get('type'),
            title=extracted_data.get('title') or 'Untitled',
            org=extracted_data.get('org'),
            deadline_iso=deadline_iso or event_date_iso,
            deadline_proximity=deadline_proximity,
            meeting_time=meeting_time,
            interview_time=interview_time,
            grant_amount=grant_amount,
            requirements=extracted_data.get('eligibility', []),
            required_docs=extracted_data.get('required_docs', []),
            link=extracted_data.get('link'),
            contact=extracted_data.get('contact'),
            location=extracted_data.get('location'),
            snippet=snippet,
        )
        
        # Step 6: Route to appropriate category list
        if category == 'opportunity':
            response.opportunities.append(categorized)
        elif category == 'meeting':
            response.meetings.append(categorized)
        elif category == 'interview':
            response.interviews.append(categorized)
        elif category == 'deadline':
            response.deadlines.append(categorized)
        elif category == 'grant':
            response.grants.append(categorized)
        else:
            response.other_important.append(categorized)
    
    # Sort each category by deadline proximity (urgent first)
    proximity_order = {'urgent': 0, 'soon': 1, 'later': 2, 'expired': 3, None: 4}
    
    for category_list in [response.opportunities, response.meetings, response.interviews, 
                          response.deadlines, response.grants, response.other_important]:
        category_list.sort(key=lambda x: proximity_order.get(x.deadline_proximity, 4))
    
    logger.info(
        f"Inbox extraction complete: {len(response.opportunities)} opportunities, "
        f"{len(response.meetings)} meetings, {len(response.interviews)} interviews, "
        f"{len(response.deadlines)} deadlines, {len(response.grants)} grants, "
        f"{len(response.other_important)} other, {len(response.discarded)} discarded, "
        f"{len(response.failed)} failed"
    )
    
    return response
