"""
Property-based tests for OpportunityAnalytics class.

Tests Properties 2, 3, 4 from the design document:
- Property 2: Analytics DataFrame Construction
- Property 3: Descriptive Statistics Validity
- Property 4: Distribution Aggregation Correctness

Requirements: 3.1, 3.2, 3.3, 3.4
"""
import pytest
from hypothesis import given, strategies as st
from hypothesis import settings
from analytics import OpportunityAnalytics
from models import RankedOpportunity, ScoreBreakdown, ScoreDetail, ActionChecklist


# Strategy for generating ScoreDetail objects
@st.composite
def score_detail_strategy(draw):
    score = draw(st.integers(min_value=0, max_value=55))
    reason = draw(st.text(min_size=1, max_size=50))
    return ScoreDetail(score=score, reason=reason)


# Strategy for generating ScoreBreakdown objects
@st.composite
def score_breakdown_strategy(draw):
    skill_score = draw(st.integers(min_value=0, max_value=55))
    urgency_score = draw(st.integers(min_value=0, max_value=15))
    type_score = draw(st.integers(min_value=0, max_value=15))
    location_score = draw(st.integers(min_value=0, max_value=10))
    financial_score = draw(st.integers(min_value=0, max_value=5))
    completeness_score = draw(st.integers(min_value=0, max_value=5))
    
    total = skill_score + urgency_score + type_score + location_score + financial_score + completeness_score
    
    return ScoreBreakdown(
        skill_alignment=ScoreDetail(score=skill_score, reason="test"),
        urgency=ScoreDetail(score=urgency_score, reason="test"),
        type_match=ScoreDetail(score=type_score, reason="test"),
        location=ScoreDetail(score=location_score, reason="test"),
        financial_bonus=ScoreDetail(score=financial_score, reason="test"),
        completeness=ScoreDetail(score=completeness_score, reason="test"),
        total=total
    )


# Strategy for generating RankedOpportunity objects
@st.composite
def ranked_opportunity_strategy(draw):
    opp_id = draw(st.integers(min_value=1, max_value=10000))
    title = draw(st.text(min_size=5, max_size=100))
    org = draw(st.text(min_size=3, max_size=50))
    opp_type = draw(st.sampled_from(['internship', 'hackathon', 'scholarship', 'competition', 'workshop']))
    urgency = draw(st.sampled_from(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']))
    score_breakdown = draw(score_breakdown_strategy())
    
    return RankedOpportunity(
        id=opp_id,
        title=title,
        org=org,
        type=opp_type,
        deadline_iso=None,
        urgency_badge=urgency,
        score_breakdown=score_breakdown,
        checklist=[],
        link=None,
        contact=None
    )


# Feature: inbox-copilot-integration, Property 2: Analytics DataFrame Construction
@given(st.lists(ranked_opportunity_strategy(), min_size=1, max_size=50))
@settings(max_examples=100)
def test_dataframe_construction(opportunities):
    """
    Property 2: For any non-empty list of ranked opportunities, converting to a pandas 
    DataFrame SHALL produce a DataFrame with rows equal to the number of opportunities 
    and columns including at minimum: id, title, org, type, score, urgency_badge.
    
    Validates: Requirements 3.1
    """
    analytics = OpportunityAnalytics(opportunities)
    df = analytics.df
    
    # Check row count matches opportunity count
    assert len(df) == len(opportunities), f"DataFrame has {len(df)} rows but expected {len(opportunities)}"
    
    # Check required columns exist
    required_columns = {'id', 'title', 'org', 'type', 'score', 'urgency_badge'}
    assert required_columns.issubset(df.columns), f"Missing columns: {required_columns - set(df.columns)}"
    
    # Verify data integrity - check first and last opportunity
    if len(opportunities) > 0:
        first_opp = opportunities[0]
        assert df.iloc[0]['id'] == first_opp.id
        assert df.iloc[0]['title'] == first_opp.title
        assert df.iloc[0]['org'] == first_opp.org
        assert df.iloc[0]['type'] == first_opp.type
        assert df.iloc[0]['score'] == first_opp.score_breakdown.total
        assert df.iloc[0]['urgency_badge'] == first_opp.urgency_badge


# Feature: inbox-copilot-integration, Property 3: Descriptive Statistics Validity
@given(st.lists(ranked_opportunity_strategy(), min_size=1, max_size=50))
@settings(max_examples=100)
def test_descriptive_statistics_validity(opportunities):
    """
    Property 3: For any non-empty set of opportunity scores, computed descriptive 
    statistics SHALL satisfy: mean is within [0, 105], standard deviation is >= 0, 
    and all percentiles are within [0, 105] and monotonically increasing.
    
    Validates: Requirements 3.2
    """
    analytics = OpportunityAnalytics(opportunities)
    stats = analytics.compute_descriptive_stats()
    
    # Check mean is in valid range
    assert 0 <= stats['mean'] <= 105, f"Mean {stats['mean']} is outside [0, 105]"
    
    # Check std is non-negative (or NaN for single value)
    import math
    assert stats['std'] >= 0 or math.isnan(stats['std']), f"Standard deviation {stats['std']} is invalid"
    
    # Check percentiles are in valid range
    percentiles = stats['percentiles']
    for p_name, p_value in percentiles.items():
        assert 0 <= p_value <= 105, f"Percentile {p_name} value {p_value} is outside [0, 105]"
    
    # Check percentiles are monotonically increasing
    p25 = percentiles['25']
    p50 = percentiles['50']
    p75 = percentiles['75']
    p90 = percentiles['90']
    
    assert p25 <= p50 <= p75 <= p90, \
        f"Percentiles not monotonic: 25th={p25}, 50th={p50}, 75th={p75}, 90th={p90}"


# Feature: inbox-copilot-integration, Property 4: Distribution Aggregation Correctness
@given(st.lists(ranked_opportunity_strategy(), min_size=1, max_size=50))
@settings(max_examples=100)
def test_distribution_aggregation_correctness(opportunities):
    """
    Property 4: For any set of opportunities, the sum of counts across all categories 
    in type_distribution SHALL equal the total number of opportunities, and the same 
    SHALL hold for urgency_distribution.
    
    Validates: Requirements 3.3, 3.4
    """
    analytics = OpportunityAnalytics(opportunities)
    
    # Test type distribution
    type_dist = analytics.get_type_distribution()
    type_sum = sum(type_dist.values())
    assert type_sum == len(opportunities), \
        f"Type distribution sum {type_sum} != opportunity count {len(opportunities)}"
    
    # Test urgency distribution
    urgency_dist = analytics.get_urgency_distribution()
    urgency_sum = sum(urgency_dist.values())
    assert urgency_sum == len(opportunities), \
        f"Urgency distribution sum {urgency_sum} != opportunity count {len(opportunities)}"
    
    # Verify all opportunities are accounted for in distributions
    assert type_sum > 0, "Type distribution is empty"
    assert urgency_sum > 0, "Urgency distribution is empty"


# Edge case: Empty opportunity list
def test_empty_opportunities():
    """Test that analytics handles empty opportunity list gracefully."""
    analytics = OpportunityAnalytics([])
    
    # DataFrame should be empty
    assert len(analytics.df) == 0
    
    # Stats should return zeros
    stats = analytics.compute_descriptive_stats()
    assert stats['mean'] == 0.0
    assert stats['std'] == 0.0
    
    # Distributions should be empty
    assert analytics.get_type_distribution() == {}
    assert analytics.get_urgency_distribution() == {}
