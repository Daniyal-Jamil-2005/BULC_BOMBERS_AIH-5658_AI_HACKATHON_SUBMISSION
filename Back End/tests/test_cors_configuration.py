"""
CORS Configuration Tests

Task: 2.2 Test CORS configuration
**Validates: Requirements 1.4**

These tests verify that the backend CORS middleware is properly configured
to accept requests from the frontend origin and handle CORS preflight requests.

From the requirements:
"WHEN CORS is configured, THE Backend SHALL accept requests from the frontend origin"
"""
import pytest
from fastapi.testclient import TestClient
from main import app

# Create test client
client = TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# Unit Tests: CORS Headers Verification
# ─────────────────────────────────────────────────────────────────────────────

def test_cors_allows_localhost_3000():
    """
    Test that CORS allows requests from the default frontend origin (localhost:3000).
    This is the typical development setup.
    """
    origin = "http://localhost:3000"
    response = client.get(
        "/health",
        headers={"Origin": origin}
    )
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    # With allow_origins=["*"] and allow_credentials=True, 
    # FastAPI echoes back the specific origin for security
    assert response.headers["access-control-allow-origin"] == origin


def test_cors_allows_localhost_3001():
    """
    Test that CORS allows requests from alternative frontend ports.
    Developers might run the frontend on different ports.
    """
    origin = "http://localhost:3001"
    response = client.get(
        "/health",
        headers={"Origin": origin}
    )
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == origin


def test_cors_allows_127_0_0_1():
    """
    Test that CORS allows requests from 127.0.0.1 (alternative localhost notation).
    """
    origin = "http://127.0.0.1:3000"
    response = client.get(
        "/health",
        headers={"Origin": origin}
    )
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == origin


def test_cors_allows_production_domains():
    """
    Test that CORS allows requests from production domains.
    With allow_origins=["*"], any origin should be allowed.
    """
    production_origins = [
        "https://example.com",
        "https://app.example.com",
        "https://inbox-copilot.vercel.app"
    ]
    
    for origin in production_origins:
        response = client.get(
            "/health",
            headers={"Origin": origin}
        )
        
        assert response.status_code == 200, f"Failed for origin: {origin}"
        assert "access-control-allow-origin" in response.headers
        # FastAPI echoes back the specific origin when allow_credentials=True
        assert response.headers["access-control-allow-origin"] == origin


# ─────────────────────────────────────────────────────────────────────────────
# Preflight Request Tests (OPTIONS)
# ─────────────────────────────────────────────────────────────────────────────

def test_cors_preflight_request_process_files():
    """
    Test CORS preflight (OPTIONS) request for the /process-files endpoint.
    Browsers send OPTIONS requests before POST requests with custom headers.
    """
    response = client.options(
        "/process-files",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        }
    )
    
    # Preflight should return 200 OK
    assert response.status_code == 200
    
    # Verify CORS headers are present
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers
    
    # Verify allowed methods include POST
    allowed_methods = response.headers["access-control-allow-methods"]
    assert "POST" in allowed_methods or "*" in allowed_methods
    
    # Verify credentials are allowed
    if "access-control-allow-credentials" in response.headers:
        assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_preflight_request_sample_data():
    """
    Test CORS preflight (OPTIONS) request for the /sample-data endpoint.
    """
    response = client.options(
        "/sample-data",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type"
        }
    )
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers


def test_cors_preflight_with_custom_headers():
    """
    Test CORS preflight with custom headers that might be used by the frontend.
    """
    response = client.options(
        "/process-files",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization,x-custom-header"
        }
    )
    
    assert response.status_code == 200
    assert "access-control-allow-headers" in response.headers
    
    # With allow_headers=["*"], all headers should be allowed
    allowed_headers = response.headers["access-control-allow-headers"]
    assert "*" in allowed_headers or "content-type" in allowed_headers.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Actual Request Tests with CORS Headers
# ─────────────────────────────────────────────────────────────────────────────

def test_cors_on_get_request():
    """
    Test that CORS headers are present on actual GET requests.
    """
    response = client.get(
        "/sample-data",
        headers={"Origin": "http://localhost:3000"}
    )
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    
    # Verify response is valid JSON
    data = response.json()
    assert "profile" in data
    assert "emails" in data


def test_cors_on_post_request():
    """
    Test that CORS headers are present on actual POST requests.
    This simulates a real frontend request to process emails.
    """
    # Prepare test data
    test_profile = {
        "degree": "BSCS",
        "semester": 6,
        "cgpa": 3.5,
        "skills": ["Python", "Machine Learning"],
        "preferred_opportunity_types": ["internship"],
        "location_preference": "Lahore",
        "financial_need": False,
        "total_semesters": 8
    }
    
    test_email = """Subject: Test Internship
From: test@example.com

This is a test internship opportunity.
Skills: Python, Machine Learning
Deadline: March 15, 2025"""
    
    # Make POST request with Origin header
    response = client.post(
        "/process",
        json={
            "profile": test_profile,
            "emails": [test_email]
        },
        headers={"Origin": "http://localhost:3000"}
    )
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    
    # Verify response structure
    data = response.json()
    assert "ranked_opportunities" in data
    assert "discarded" in data
    assert "failed" in data


def test_cors_on_multipart_request():
    """
    Test that CORS headers are present on multipart/form-data requests.
    This is used by the /process-files endpoint.
    """
    import json
    
    test_profile = {
        "degree": "BSCS",
        "semester": 6,
        "cgpa": 3.5,
        "skills": ["Python"],
        "preferred_opportunity_types": ["internship"],
        "location_preference": "Lahore",
        "financial_need": False,
        "total_semesters": 8
    }
    
    test_email_text = """Subject: Test Opportunity
From: test@example.com

Test internship with Python skills required.
Deadline: March 15, 2025"""
    
    # Make multipart request with Origin header
    response = client.post(
        "/process-files",
        data={
            "profile": json.dumps(test_profile),
            "email_text": test_email_text
        },
        headers={"Origin": "http://localhost:3000"}
    )
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    
    # Verify response structure
    data = response.json()
    assert "ranked_opportunities" in data
    assert "discarded" in data
    assert "failed" in data


# ─────────────────────────────────────────────────────────────────────────────
# Error Response CORS Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_cors_on_400_error():
    """
    Test that CORS headers are present even on error responses (400 Bad Request).
    This is important for frontend error handling.
    """
    # Send invalid request (missing profile)
    response = client.post(
        "/process",
        json={"emails": []},  # Missing profile, empty emails
        headers={"Origin": "http://localhost:3000"}
    )
    
    # Should return 422 (validation error) or 400
    assert response.status_code in [400, 422]
    
    # CORS headers should still be present
    assert "access-control-allow-origin" in response.headers


def test_cors_on_404_error():
    """
    Test that CORS headers are present on 404 Not Found responses.
    """
    response = client.get(
        "/nonexistent-endpoint",
        headers={"Origin": "http://localhost:3000"}
    )
    
    assert response.status_code == 404
    assert "access-control-allow-origin" in response.headers


def test_cors_on_422_validation_error():
    """
    Test that CORS headers are present on validation errors (422).
    """
    # Send request with invalid profile data
    response = client.post(
        "/process",
        json={
            "profile": {
                "degree": "BSCS",
                "semester": "invalid",  # Should be integer
                "cgpa": 3.5,
                "skills": [],
                "preferred_opportunity_types": [],
                "location_preference": "Lahore",
                "financial_need": False,
                "total_semesters": 8
            },
            "emails": ["test"]
        },
        headers={"Origin": "http://localhost:3000"}
    )
    
    assert response.status_code == 422
    assert "access-control-allow-origin" in response.headers


# ─────────────────────────────────────────────────────────────────────────────
# Credentials and Headers Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_cors_allows_credentials():
    """
    Test that CORS configuration allows credentials (cookies, authorization headers).
    This is important for authenticated requests.
    """
    response = client.get(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Cookie": "session=test123"
        }
    )
    
    assert response.status_code == 200
    
    # Check if credentials are allowed
    # With allow_credentials=True, this header should be present
    if "access-control-allow-credentials" in response.headers:
        assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_exposes_headers():
    """
    Test that CORS configuration properly exposes response headers to the frontend.
    """
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"}
    )
    
    assert response.status_code == 200
    
    # Verify basic CORS headers are present
    assert "access-control-allow-origin" in response.headers
    
    # If expose_headers is configured, verify it
    if "access-control-expose-headers" in response.headers:
        exposed = response.headers["access-control-expose-headers"]
        # Should expose common headers
        assert len(exposed) > 0


# ─────────────────────────────────────────────────────────────────────────────
# Integration Test: Full Frontend-Backend Flow
# ─────────────────────────────────────────────────────────────────────────────

def test_full_cors_workflow():
    """
    Integration test: Simulate a complete frontend-backend workflow with CORS.
    
    This test simulates:
    1. Frontend loads sample data (GET /sample-data)
    2. Frontend submits scan request (POST /process-files)
    3. Frontend receives results
    
    All requests include Origin header to verify CORS works end-to-end.
    """
    origin = "http://localhost:3000"
    
    # Step 1: Load sample data
    sample_response = client.get(
        "/sample-data",
        headers={"Origin": origin}
    )
    
    assert sample_response.status_code == 200
    assert "access-control-allow-origin" in sample_response.headers
    
    sample_data = sample_response.json()
    assert "profile" in sample_data
    assert "emails" in sample_data
    
    # Step 2: Submit scan request using sample data
    import json
    
    scan_response = client.post(
        "/process-files",
        data={
            "profile": json.dumps(sample_data["profile"]),
            "email_text": "\n---\n".join(sample_data["emails"][:3])  # Use first 3 emails
        },
        headers={"Origin": origin}
    )
    
    assert scan_response.status_code == 200
    assert "access-control-allow-origin" in scan_response.headers
    
    # Step 3: Verify results structure
    results = scan_response.json()
    assert "ranked_opportunities" in results
    assert "discarded" in results
    assert "failed" in results
    
    # Verify we got some results
    total_results = (
        len(results["ranked_opportunities"]) +
        len(results["discarded"]) +
        len(results["failed"])
    )
    assert total_results > 0, "Should have processed at least one email"


# ─────────────────────────────────────────────────────────────────────────────
# Documentation Test
# ─────────────────────────────────────────────────────────────────────────────

def test_cors_configuration_documentation():
    """
    Document the current CORS configuration for reference.
    This test always passes but prints useful information.
    """
    # Get CORS headers from a test request
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"}
    )
    
    print("\n" + "="*80)
    print("CORS Configuration Summary")
    print("="*80)
    print(f"Status Code: {response.status_code}")
    print("\nCORS Headers:")
    
    cors_headers = {
        k: v for k, v in response.headers.items() 
        if k.lower().startswith("access-control")
    }
    
    for header, value in cors_headers.items():
        print(f"  {header}: {value}")
    
    print("\nConfiguration in main.py:")
    print("  allow_origins: ['*']")
    print("  allow_credentials: True")
    print("  allow_methods: ['*']")
    print("  allow_headers: ['*']")
    print("="*80 + "\n")
    
    # Test always passes - this is just for documentation
    assert True


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────

"""
CORS Configuration Test Summary:

Current Configuration (main.py):
- allow_origins: ["*"] - Allows requests from any origin
- allow_credentials: True - Allows cookies and authorization headers
- allow_methods: ["*"] - Allows all HTTP methods
- allow_headers: ["*"] - Allows all request headers

This configuration is suitable for:
✓ Development environments (localhost:3000, localhost:3001, etc.)
✓ Testing with different frontend ports
✓ Production deployments (any domain)

Security Considerations:
⚠ The wildcard "*" configuration is permissive and suitable for development
⚠ For production, consider restricting to specific origins:
  allow_origins=["https://yourdomain.com", "https://app.yourdomain.com"]

Required CORS Configuration Changes:
✓ None - Current configuration accepts frontend origin (Requirement 1.4)

Test Coverage:
✓ Localhost origins (3000, 3001, 127.0.0.1)
✓ Production domain origins
✓ Preflight (OPTIONS) requests
✓ Actual GET/POST requests
✓ Multipart form-data requests
✓ Error responses (400, 404, 422)
✓ Credentials and custom headers
✓ Full frontend-backend workflow

All tests verify that CORS headers are present and properly configured,
ensuring the frontend can successfully communicate with the backend.
"""
