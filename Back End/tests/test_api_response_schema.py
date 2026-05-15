"""
Property-based tests for API response schema consistency.

Feature: inbox-copilot-integration
Property 1: API Response Schema Consistency

**Validates: Requirements 1.2**

From the design document:
"For any valid scan request to the backend, the response SHALL contain exactly 
three top-level fields: `ranked_opportunities`, `discarded`, and `failed`, 
each containing arrays of the appropriate type."
"""
import pytest
from hypothesis import given, strategies as st, settings
from typing import List
from unittest.mock import patch, MagicMock

from models import (
    ProcessRequest,
    ProcessResponse,
    StudentProfile,
    RankedOpportunity,
    DiscardedOpportunity,
    FailedOpportunity,
)
from main import process_emails_logic


# ─────────────────────────────────────────────────────────────────────────────
# Mock LLM Extraction for Fast Testing
# ─────────────────────────────────────────────────────────────────────────────

def mock_extract_opportunity(email_text: str):
    """
    Mock LLM extraction that returns deterministic results based on email content.
    This allows property tests to run quickly without actual LLM calls.
    """
    email_lower = email_text.lower()
    
    # Determine if it's an opportunity based on keywords
    opportunity_keywords = ['internship', 'hackathon', 'scholarship', 'fellowship', 
                           'grant', 'deadline', 'apply', 'skills', 'requirements']
    non_opportunity_keywords = ['cafeteria', 'menu', 'library', 'fine', 'cancelled', 
                               'lost', 'found', 'election', 'vote']
    
    is_opportunity = any(keyword in email_lower for keyword in opportunity_keywords)
    is_non_opportunity = any(keyword in email_lower for keyword in non_opportunity_keywords)
    
    if is_non_opportunity:
        return {"is_opportunity": False}
    
    if not is_opportunity:
        # Return None to simulate LLM failure for ambiguous emails
        return None
    
    # Extract basic information
    return {
        "is_opportunity": True,
        "type": "internship" if "internship" in email_lower else 
                "hackathon" if "hackathon" in email_lower else
                "scholarship" if "scholarship" in email_lower else "other",
        "title": "Test Opportunity",
        "org": "Test Organization",
        "deadline_raw": "March 15, 2025" if "deadline" in email_lower else None,
        "eligibility": ["Python", "Machine Learning"] if "skills" in email_lower or "python" in email_lower else [],
        "required_docs": ["Resume"] if "resume" in email_lower else [],
        "link": "https://example.com",
        "contact": "test@example.com",
        "min_cgpa": 3.0 if "cgpa" in email_lower or "3.0" in email_lower else None,
        "mandatory_language": None,
        "degree_restrictions": ["BSCS"] if "bscs" in email_lower else [],
        "graduation_year_restriction": None,
        "location": "Lahore" if "lahore" in email_lower else "Remote",
        "is_scholarship_or_grant": "scholarship" in email_lower or "grant" in email_lower
    }


# ─────────────────────────────────────────────────────────────────────────────
# Hypothesis Strategies for generating test data
# ─────────────────────────────────────────────────────────────────────────────

@st.composite
def student_profile_strategy(draw):
    """Generate valid StudentProfile instances."""
    degrees = ["BSCS", "BSEE", "BSAI", "BSSE", "BSDS", "BSMATH", "BSPHY"]
    opportunity_types = ["internship", "hackathon", "scholarship", "fellowship", "grant"]
    locations = ["Lahore", "Karachi", "Islamabad", "Remote", "Hybrid"]
    
    # Generate a list of common skills
    all_skills = [
        "Python", "Java", "JavaScript", "C++", "React", "Node.js",
        "Machine Learning", "Data Science", "Cloud Computing", "AWS",
        "Docker", "Kubernetes", "SQL", "MongoDB", "Git"
    ]
    
    return StudentProfile(
        degree=draw(st.sampled_from(degrees)),
        semester=draw(st.integers(min_value=1, max_value=8)),
        cgpa=draw(st.floats(min_value=2.0, max_value=4.0)),
        skills=draw(st.lists(st.sampled_from(all_skills), min_size=1, max_size=10, unique=True)),
        preferred_opportunity_types=draw(st.lists(
            st.sampled_from(opportunity_types), 
            min_size=1, 
            max_size=len(opportunity_types),
            unique=True
        )),
        location_preference=draw(st.sampled_from(locations)),
        financial_need=draw(st.booleans()),
        total_semesters=draw(st.integers(min_value=6, max_value=10))
    )


@st.composite
def email_text_strategy(draw):
    """
    Generate email text that could be opportunities or non-opportunities.
    This creates realistic email content for testing.
    """
    email_types = [
        # Opportunity emails
        """Subject: Software Engineering Internship at TechCorp
From: hr@techcorp.com

We are looking for talented students for a summer internship.
Requirements: Python, React, 3.0+ CGPA
Deadline: Apply by March 15, 2025
Location: Lahore
Contact: careers@techcorp.com""",
        
        """Subject: National AI Hackathon 2025
From: events@aihackathon.pk

Join us for the biggest AI hackathon of the year!
Open to all university students.
Prize pool: PKR 500,000
Deadline: Registration closes in 10 days
Location: Remote
Skills: Machine Learning, Python, Data Science""",
        
        """Subject: Merit Scholarship for CS Students
From: scholarships@university.edu

Full tuition scholarship available for exceptional CS students.
Requirements: CGPA 3.5+, BSCS degree
Deadline: April 30, 2025
This is a scholarship opportunity.
Apply at: https://university.edu/scholarships""",
        
        # Non-opportunity emails
        """Subject: Cafeteria Menu Update
From: admin@university.edu

New menu items available starting next week.
Try our special biryani!
Open 8am - 8pm daily.""",
        
        """Subject: Library Fine Reminder
From: library@university.edu

You have an outstanding fine of PKR 200.
Please clear it at the library counter.""",
        
        """Subject: Class Cancelled Tomorrow
From: professor@university.edu

The CS101 class scheduled for tomorrow is cancelled.
We will reschedule next week.""",
    ]
    
    return draw(st.sampled_from(email_types))


@st.composite
def process_request_strategy(draw):
    """Generate valid ProcessRequest instances with varying email lists."""
    profile = draw(student_profile_strategy())
    
    # Generate between 1 and 10 emails (at least 1 to avoid HTTPException)
    num_emails = draw(st.integers(min_value=1, max_value=10))
    emails = [draw(email_text_strategy()) for _ in range(num_emails)]
    
    return ProcessRequest(profile=profile, emails=emails)


# ─────────────────────────────────────────────────────────────────────────────
# Property Test: API Response Schema Consistency
# ─────────────────────────────────────────────────────────────────────────────

@settings(max_examples=100, deadline=None)
@given(request=process_request_strategy())
@patch('main.extract_opportunity', side_effect=mock_extract_opportunity)
def test_api_response_schema_consistency(mock_extract, request: ProcessRequest):
    """
    Property 1: API Response Schema Consistency
    
    **Validates: Requirements 1.2**
    
    For any valid scan request to the backend, the response SHALL contain exactly 
    three top-level fields: `ranked_opportunities`, `discarded`, and `failed`, 
    each containing arrays of the appropriate type.
    
    This property verifies that:
    1. The response always has exactly three top-level fields
    2. Each field is a list (array)
    3. ranked_opportunities contains RankedOpportunity objects
    4. discarded contains DiscardedOpportunity objects
    5. failed contains FailedOpportunity objects
    6. No additional fields are present
    
    Note: This test mocks the LLM extraction to run quickly (100+ iterations).
    """
    # Execute the processing logic
    response = process_emails_logic(request)
    
    # Property 1.1: Response must be a ProcessResponse instance
    assert isinstance(response, ProcessResponse), \
        "Response must be a ProcessResponse instance"
    
    # Property 1.2: Response must have exactly three top-level fields
    response_dict = response.model_dump()
    expected_fields = {"ranked_opportunities", "discarded", "failed"}
    actual_fields = set(response_dict.keys())
    
    assert actual_fields == expected_fields, \
        f"Response must have exactly these fields: {expected_fields}, got: {actual_fields}"
    
    # Property 1.3: Each field must be a list
    assert isinstance(response.ranked_opportunities, list), \
        "ranked_opportunities must be a list"
    assert isinstance(response.discarded, list), \
        "discarded must be a list"
    assert isinstance(response.failed, list), \
        "failed must be a list"
    
    # Property 1.4: ranked_opportunities must contain only RankedOpportunity objects
    for item in response.ranked_opportunities:
        assert isinstance(item, RankedOpportunity), \
            f"ranked_opportunities must contain only RankedOpportunity objects, got {type(item)}"
    
    # Property 1.5: discarded must contain only DiscardedOpportunity objects
    for item in response.discarded:
        assert isinstance(item, DiscardedOpportunity), \
            f"discarded must contain only DiscardedOpportunity objects, got {type(item)}"
    
    # Property 1.6: failed must contain only FailedOpportunity objects
    for item in response.failed:
        assert isinstance(item, FailedOpportunity), \
            f"failed must contain only FailedOpportunity objects, got {type(item)}"
    
    # Property 1.7: Total count should match input email count
    total_processed = (
        len(response.ranked_opportunities) + 
        len(response.discarded) + 
        len(response.failed)
    )
    assert total_processed == len(request.emails), \
        f"Total processed ({total_processed}) must equal input emails ({len(request.emails)})"
    
    # Property 1.8: All IDs should be unique and within valid range
    all_ids = (
        [opp.id for opp in response.ranked_opportunities] +
        [opp.id for opp in response.discarded] +
        [opp.id for opp in response.failed]
    )
    
    assert len(all_ids) == len(set(all_ids)), \
        "All opportunity IDs must be unique"
    
    for id_val in all_ids:
        assert 0 <= id_val < len(request.emails), \
            f"ID {id_val} must be within range [0, {len(request.emails)})"


# ─────────────────────────────────────────────────────────────────────────────
# Additional Unit Tests for Edge Cases
# ─────────────────────────────────────────────────────────────────────────────

def test_response_schema_with_single_email():
    """Unit test: Verify schema with a single email."""
    profile = StudentProfile(
        degree="BSCS",
        semester=6,
        cgpa=3.5,
        skills=["Python", "Machine Learning"],
        preferred_opportunity_types=["internship"],
        location_preference="Lahore",
        financial_need=False,
        total_semesters=8
    )
    
    request = ProcessRequest(
        profile=profile,
        emails=["""Subject: Test Internship
From: test@example.com

This is a test internship opportunity.
Skills: Python, Machine Learning
Deadline: March 15, 2025"""]
    )
    
    response = process_emails_logic(request)
    
    # Verify schema
    assert hasattr(response, 'ranked_opportunities')
    assert hasattr(response, 'discarded')
    assert hasattr(response, 'failed')
    assert isinstance(response.ranked_opportunities, list)
    assert isinstance(response.discarded, list)
    assert isinstance(response.failed, list)
    
    # Verify total count
    total = len(response.ranked_opportunities) + len(response.discarded) + len(response.failed)
    assert total == 1


def test_response_schema_with_mixed_emails():
    """Unit test: Verify schema with a mix of opportunities and non-opportunities."""
    profile = StudentProfile(
        degree="BSCS",
        semester=6,
        cgpa=3.5,
        skills=["Python"],
        preferred_opportunity_types=["internship"],
        location_preference="Lahore",
        financial_need=False,
        total_semesters=8
    )
    
    request = ProcessRequest(
        profile=profile,
        emails=[
            """Subject: Internship Opportunity
From: hr@company.com
Skills: Python
Deadline: March 15, 2025""",
            
            """Subject: Cafeteria Menu
From: admin@university.edu
New menu available next week.""",
            
            """Subject: Invalid Email
This is not a properly formatted email."""
        ]
    )
    
    response = process_emails_logic(request)
    
    # Verify schema consistency
    assert isinstance(response, ProcessResponse)
    assert len(response.ranked_opportunities) + len(response.discarded) + len(response.failed) == 3
    
    # Verify each list contains correct types
    for opp in response.ranked_opportunities:
        assert isinstance(opp, RankedOpportunity)
    for opp in response.discarded:
        assert isinstance(opp, DiscardedOpportunity)
    for opp in response.failed:
        assert isinstance(opp, FailedOpportunity)
