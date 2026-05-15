"""
Unit tests for /scan-gmail endpoint

Tests the Gmail scanning endpoint integration with the scoring engine.
Validates requirements 9.4 and 9.5.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from models import ScanEmailRequest, StudentProfile, ProcessResponse

client = TestClient(app)


@pytest.fixture
def sample_profile():
    """Sample student profile for testing"""
    return {
        "degree": "BSCS",
        "semester": 6,
        "cgpa": 3.4,
        "skills": ["Python", "Cloud Security", "React"],
        "preferred_opportunity_types": ["internship", "hackathon"],
        "location_preference": "Lahore",
        "financial_need": True,
        "total_semesters": 8
    }


@pytest.fixture
def sample_credentials():
    """Sample Gmail OAuth credentials"""
    return {
        "access_token": "test_access_token_12345",
        "refresh_token": "test_refresh_token_67890",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "test_client_id",
        "client_secret": "test_client_secret"
    }


@pytest.fixture
def sample_emails():
    """Sample email texts extracted from Gmail"""
    return [
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
Contact: hackathon@nca.gov.pk"""
    ]


class TestScanGmailEndpoint:
    """Test suite for /scan-gmail endpoint"""
    
    def test_scan_gmail_success(self, sample_profile, sample_credentials, sample_emails):
        """
        Test successful Gmail scan with valid credentials and emails.
        
        Validates:
        - Endpoint accepts valid ScanEmailRequest
        - Returns ProcessResponse with ranked_opportunities
        - Response structure matches /process-files format
        
        Requirements: 9.4, 9.5
        """
        # Mock the GmailScanner and EmailProcessor
        with patch('main.GmailScanner') as MockGmailScanner, \
             patch('main.EmailProcessor') as MockEmailProcessor:
            
            # Setup mocks
            mock_scanner = Mock()
            MockGmailScanner.return_value = mock_scanner
            
            mock_processor = Mock()
            mock_processor.scan_and_process.return_value = {
                'emails': sample_emails,
                'total_fetched': 2,
                'successfully_extracted': 2
            }
            MockEmailProcessor.return_value = mock_processor
            
            # Make request
            request_data = {
                "provider": "gmail",
                "credentials": sample_credentials,
                "profile": sample_profile,
                "max_emails": 100
            }
            
            response = client.post("/scan-gmail", json=request_data)
            
            # Assertions
            assert response.status_code == 200
            
            data = response.json()
            assert "ranked_opportunities" in data
            assert "discarded" in data
            assert "failed" in data
            
            # Verify response structure matches ProcessResponse
            assert isinstance(data["ranked_opportunities"], list)
            assert isinstance(data["discarded"], list)
            assert isinstance(data["failed"], list)
            
            # Verify mocks were called correctly
            MockGmailScanner.assert_called_once_with(sample_credentials)
            MockEmailProcessor.assert_called_once_with(mock_scanner)
            mock_processor.scan_and_process.assert_called_once()
    
    def test_scan_gmail_invalid_provider(self, sample_profile, sample_credentials):
        """
        Test that endpoint rejects non-gmail providers.
        
        Validates:
        - Endpoint validates provider field
        - Returns 400 error for invalid provider
        
        Requirements: 9.4
        """
        request_data = {
            "provider": "outlook",  # Invalid for this endpoint
            "credentials": sample_credentials,
            "profile": sample_profile,
            "max_emails": 100
        }
        
        response = client.post("/scan-gmail", json=request_data)
        
        assert response.status_code == 400
        assert "Invalid provider" in response.json()["detail"]
    
    def test_scan_gmail_invalid_credentials(self, sample_profile):
        """
        Test handling of invalid Gmail credentials.
        
        Validates:
        - Endpoint handles authentication errors
        - Returns 400 error with descriptive message
        
        Requirements: 9.6
        """
        with patch('main.GmailScanner') as MockGmailScanner:
            # Mock scanner to raise ValueError on invalid credentials
            mock_scanner = Mock()
            mock_scanner.authenticate.side_effect = ValueError("Missing required field: access_token")
            MockGmailScanner.return_value = mock_scanner
            
            with patch('main.EmailProcessor') as MockEmailProcessor:
                mock_processor = Mock()
                mock_processor.scan_and_process.side_effect = ValueError("Missing required field: access_token")
                MockEmailProcessor.return_value = mock_processor
                
                request_data = {
                    "provider": "gmail",
                    "credentials": {},  # Empty credentials
                    "profile": sample_profile,
                    "max_emails": 100
                }
                
                response = client.post("/scan-gmail", json=request_data)
                
                assert response.status_code == 400
                assert "Invalid credentials" in response.json()["detail"]
    
    def test_scan_gmail_no_emails_found(self, sample_profile, sample_credentials):
        """
        Test handling when no emails are found in Gmail inbox.
        
        Validates:
        - Endpoint handles empty email list gracefully
        - Returns empty ProcessResponse
        
        Requirements: 9.4
        """
        with patch('main.GmailScanner') as MockGmailScanner, \
             patch('main.EmailProcessor') as MockEmailProcessor:
            
            # Setup mocks to return empty email list
            mock_scanner = Mock()
            MockGmailScanner.return_value = mock_scanner
            
            mock_processor = Mock()
            mock_processor.scan_and_process.return_value = {
                'emails': [],
                'total_fetched': 0,
                'successfully_extracted': 0
            }
            MockEmailProcessor.return_value = mock_processor
            
            request_data = {
                "provider": "gmail",
                "credentials": sample_credentials,
                "profile": sample_profile,
                "max_emails": 100
            }
            
            response = client.post("/scan-gmail", json=request_data)
            
            assert response.status_code == 200
            
            data = response.json()
            assert len(data["ranked_opportunities"]) == 0
            assert len(data["discarded"]) == 0
            assert len(data["failed"]) == 0
    
    def test_scan_gmail_api_error(self, sample_profile, sample_credentials):
        """
        Test handling of Gmail API errors.
        
        Validates:
        - Endpoint handles API errors gracefully
        - Returns 500 error with descriptive message
        
        Requirements: 9.6
        """
        with patch('main.GmailScanner') as MockGmailScanner, \
             patch('main.EmailProcessor') as MockEmailProcessor:
            
            # Mock processor to raise exception
            mock_scanner = Mock()
            MockGmailScanner.return_value = mock_scanner
            
            mock_processor = Mock()
            mock_processor.scan_and_process.side_effect = Exception("Gmail API quota exceeded")
            MockEmailProcessor.return_value = mock_processor
            
            request_data = {
                "provider": "gmail",
                "credentials": sample_credentials,
                "profile": sample_profile,
                "max_emails": 100
            }
            
            response = client.post("/scan-gmail", json=request_data)
            
            assert response.status_code == 500
            assert "Failed to scan Gmail" in response.json()["detail"]
    
    def test_scan_gmail_custom_max_emails(self, sample_profile, sample_credentials, sample_emails):
        """
        Test that max_emails parameter is respected.
        
        Validates:
        - Endpoint passes max_emails to scanner
        - Scanner respects the limit
        
        Requirements: 9.4
        """
        with patch('main.GmailScanner') as MockGmailScanner, \
             patch('main.EmailProcessor') as MockEmailProcessor:
            
            mock_scanner = Mock()
            MockGmailScanner.return_value = mock_scanner
            
            mock_processor = Mock()
            mock_processor.scan_and_process.return_value = {
                'emails': sample_emails[:1],  # Only 1 email
                'total_fetched': 1,
                'successfully_extracted': 1
            }
            MockEmailProcessor.return_value = mock_processor
            
            request_data = {
                "provider": "gmail",
                "credentials": sample_credentials,
                "profile": sample_profile,
                "max_emails": 50  # Custom limit
            }
            
            response = client.post("/scan-gmail", json=request_data)
            
            assert response.status_code == 200
            
            # Verify max_emails was passed to processor
            call_args = mock_processor.scan_and_process.call_args
            assert call_args[1]['max_emails'] == 50
    
    def test_scan_gmail_response_format_matches_process_files(self, sample_profile, sample_credentials, sample_emails):
        """
        Test that /scan-gmail response format matches /process-files.
        
        Validates:
        - Response structure is identical to /process-files
        - All required fields are present
        - Field types match ProcessResponse model
        
        Requirements: 9.5
        """
        with patch('main.GmailScanner') as MockGmailScanner, \
             patch('main.EmailProcessor') as MockEmailProcessor:
            
            mock_scanner = Mock()
            MockGmailScanner.return_value = mock_scanner
            
            mock_processor = Mock()
            mock_processor.scan_and_process.return_value = {
                'emails': sample_emails,
                'total_fetched': 2,
                'successfully_extracted': 2
            }
            MockEmailProcessor.return_value = mock_processor
            
            request_data = {
                "provider": "gmail",
                "credentials": sample_credentials,
                "profile": sample_profile,
                "max_emails": 100
            }
            
            response = client.post("/scan-gmail", json=request_data)
            
            assert response.status_code == 200
            
            data = response.json()
            
            # Verify all required top-level fields
            assert "ranked_opportunities" in data
            assert "discarded" in data
            assert "failed" in data
            
            # Verify field types
            assert isinstance(data["ranked_opportunities"], list)
            assert isinstance(data["discarded"], list)
            assert isinstance(data["failed"], list)
            
            # If there are ranked opportunities, verify structure
            if data["ranked_opportunities"]:
                opp = data["ranked_opportunities"][0]
                assert "id" in opp
                assert "title" in opp
                assert "org" in opp
                assert "type" in opp
                assert "score_breakdown" in opp
                assert "checklist" in opp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
