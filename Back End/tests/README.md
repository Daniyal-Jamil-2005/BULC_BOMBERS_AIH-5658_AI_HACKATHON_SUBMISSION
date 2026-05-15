# Test Suite for Inbox Copilot Backend

## Overview

This directory contains the test suite for the Inbox Copilot backend, including property-based tests using Hypothesis and unit tests using pytest.

## Test Structure

```
tests/
├── __init__.py                      # Package initialization
├── conftest.py                      # Pytest configuration and fixtures
├── test_api_response_schema.py      # Property tests for API response schema
└── README.md                        # This file
```

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run specific test file
```bash
pytest tests/test_api_response_schema.py -v
```

### Run with coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

## Property-Based Tests

### test_api_response_schema.py

**Property 1: API Response Schema Consistency**

Validates Requirements 1.2 from the design document:
> "For any valid scan request to the backend, the response SHALL contain exactly three top-level fields: `ranked_opportunities`, `discarded`, and `failed`, each containing arrays of the appropriate type."

**Test Configuration:**
- Framework: Hypothesis
- Iterations: 100+ examples per test run
- Mock Strategy: LLM extraction is mocked for fast execution

**What it tests:**
1. Response always has exactly three top-level fields
2. Each field is a list (array)
3. `ranked_opportunities` contains only RankedOpportunity objects
4. `discarded` contains only DiscardedOpportunity objects
5. `failed` contains only FailedOpportunity objects
6. No additional fields are present
7. Total processed count matches input email count
8. All IDs are unique and within valid range

**Test Strategies:**
- `student_profile_strategy()`: Generates valid StudentProfile instances with random degrees, semesters, CGPAs, skills, and preferences
- `email_text_strategy()`: Generates realistic email content (opportunities and non-opportunities)
- `process_request_strategy()`: Generates complete ProcessRequest instances with 1-10 emails

**Mock Implementation:**
The test uses a mock LLM extraction function (`mock_extract_opportunity`) that:
- Deterministically classifies emails based on keywords
- Returns structured opportunity data for opportunity emails
- Returns `{"is_opportunity": False}` for non-opportunity emails
- Returns `None` to simulate LLM failures for ambiguous emails

This allows the property test to run 100+ iterations in seconds instead of minutes.

## Unit Tests

### test_response_schema_with_single_email
Tests the API response schema with a single email input to verify basic functionality.

### test_response_schema_with_mixed_emails
Tests the API response schema with a mix of opportunities, non-opportunities, and invalid emails to verify proper categorization.

## Dependencies

- pytest==8.0.0
- hypothesis==6.98.0
- pytest-cov==4.1.0

## Test Coverage Goals

- Backend: 80%+ line coverage
- Critical paths (scoring, analytics): 100% coverage
- All 29 correctness properties implemented (this is Property 1)

## Notes

- Property tests use mocking to avoid slow LLM API calls during testing
- Tests follow the design document's property specifications exactly
- Each property test includes a comment tag linking to the design document property
- Tests are designed to be fast, deterministic, and comprehensive
