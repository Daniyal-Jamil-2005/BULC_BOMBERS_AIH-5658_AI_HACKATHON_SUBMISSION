"""
Email Scanner Module for Gmail and Outlook Integration

This module provides classes for scanning emails from Gmail and Outlook accounts
using their respective APIs. It handles authentication, email fetching, and content extraction.

Supports both OAuth 2.0 and App Password authentication methods.

Requirements validated: 9.2, 9.3, 9.6
"""

from typing import List, Dict, Any, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import email
from email.mime.text import MIMEText
import imaplib
import logging
from email_preprocessor import clean_email_payload
from imap_config import get_imap_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GmailScanner:
    """
    Universal email scanner supporting Gmail and other IMAP-compatible providers.
    
    Handles authentication via:
    - OAuth 2.0 (Gmail API) - requires access_token (Gmail only)
    - App Password (IMAP) - requires email and password (works with any provider)
    
    Supported providers:
    - Gmail, Yahoo, Outlook/Hotmail, iCloud, AOL, Zoho, ProtonMail, FastMail
    - Any custom email server with IMAP support
    
    Requirements: 9.2, 9.3, 9.6
    """
    
    def __init__(self, credentials: Dict[str, str], imap_server: str = None, imap_port: int = None):
        """
        Initialize email scanner with credentials.
        
        Args:
            credentials: Dictionary containing authentication credentials
                OAuth 2.0 mode (Gmail only):
                    - access_token: OAuth 2.0 access token
                    - refresh_token: OAuth 2.0 refresh token (optional)
                    - token_uri: Token endpoint URI (optional)
                    - client_id: OAuth client ID (optional)
                    - client_secret: OAuth client secret (optional)
                
                App Password mode (Universal):
                    - email: Email address (e.g., user@domain.com)
                    - password: App-specific password (16-character code)
            
            imap_server: IMAP server hostname (optional, auto-detected from email)
            imap_port: IMAP port (optional, default: 993 for SSL)
        """
        self.credentials = credentials
        self.service = None
        self.imap_connection = None
        self.auth_mode = None  # 'oauth' or 'app_password'
        self.imap_server = imap_server
        self.imap_port = imap_port or 993
        
        # Auto-detect IMAP server if using app password mode
        if not imap_server and credentials.get('email'):
            try:
                detected_host, detected_port, _ = get_imap_config(credentials['email'])
                self.imap_server = detected_host
                self.imap_port = detected_port
                logger.info(f"Auto-detected IMAP server: {self.imap_server}:{self.imap_port}")
            except Exception as e:
                logger.warning(f"Could not auto-detect IMAP server: {e}")
                self.imap_server = 'imap.gmail.com'  # Fallback to Gmail
        
        logger.info("GmailScanner initialized")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail using OAuth 2.0 or App Password.
        
        Automatically detects authentication mode based on credentials provided.
        
        Returns:
            bool: True if authentication successful, False otherwise
            
        Raises:
            ValueError: If credentials are missing required fields
            Exception: If authentication fails
        """
        # Detect authentication mode
        if self.credentials.get('access_token'):
            return self._authenticate_oauth()
        elif self.credentials.get('email') and self.credentials.get('password'):
            return self._authenticate_app_password()
        else:
            raise ValueError(
                "Invalid credentials format. Provide either:\n"
                "- OAuth: access_token (+ optional refresh_token, client_id, client_secret)\n"
                "- App Password: email + password"
            )
    
    def _authenticate_oauth(self) -> bool:
        """Authenticate using OAuth 2.0 (Gmail API)."""
        try:
            logger.info("Authenticating with OAuth 2.0")
            
            # Create credentials object
            creds = Credentials(
                token=self.credentials.get('access_token'),
                refresh_token=self.credentials.get('refresh_token'),
                token_uri=self.credentials.get('token_uri', 'https://oauth2.googleapis.com/token'),
                client_id=self.credentials.get('client_id'),
                client_secret=self.credentials.get('client_secret')
            )
            
            # Build Gmail API service
            self.service = build('gmail', 'v1', credentials=creds)
            
            # Test authentication
            profile = self.service.users().getProfile(userId='me').execute()
            logger.info(f"Successfully authenticated Gmail account via OAuth: {profile.get('emailAddress')}")
            
            self.auth_mode = 'oauth'
            return True
            
        except HttpError as e:
            error_details = e.error_details if hasattr(e, 'error_details') else str(e)
            logger.error(f"Gmail API authentication error: {error_details}")
            
            if e.resp.status == 401:
                raise Exception(
                    "OAuth authentication failed: Invalid or expired access token. "
                    "Please regenerate your OAuth token."
                )
            elif e.resp.status == 403:
                raise Exception(
                    "OAuth authentication failed: Insufficient permissions. "
                    "Please ensure Gmail API is enabled and you have granted the necessary scopes."
                )
            else:
                raise Exception(f"Gmail API error: {error_details}")
                
        except Exception as e:
            logger.error(f"OAuth authentication error: {str(e)}")
            raise Exception(f"Failed to authenticate with Gmail OAuth: {str(e)}")
    
    def _authenticate_app_password(self) -> bool:
        """Authenticate using App Password (IMAP) - works with any email provider."""
        try:
            logger.info(f"Authenticating with IMAP server: {self.imap_server}:{self.imap_port}")
            
            email_address = self.credentials.get('email')
            password = self.credentials.get('password')
            
            # Remove spaces from app password (some providers show them with spaces)
            password = password.replace(' ', '')
            
            # Connect to IMAP server
            self.imap_connection = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            
            # Login
            self.imap_connection.login(email_address, password)
            
            logger.info(f"Successfully authenticated email account via IMAP: {email_address}")
            
            self.auth_mode = 'app_password'
            return True
            
        except imaplib.IMAP4.error as e:
            error_msg = str(e)
            logger.error(f"IMAP authentication error: {error_msg}")
            
            if 'AUTHENTICATIONFAILED' in error_msg.upper():
                raise Exception(
                    f"App Password authentication failed for {self.imap_server}. "
                    "Please verify:\n"
                    "1. You're using an App Password (not your regular email password)\n"
                    "2. 2-Step Verification is enabled on your account\n"
                    "3. The app password is correct\n"
                    "4. IMAP access is enabled in your email settings"
                )
            else:
                raise Exception(f"IMAP authentication failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"App Password authentication error: {str(e)}")
            raise Exception(f"Failed to authenticate with {self.imap_server}: {str(e)}")
    
    def fetch_emails(self, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch last N emails from Gmail inbox.
        
        Supports both OAuth (Gmail API) and App Password (IMAP) modes.
        
        Args:
            max_results: Maximum number of emails to fetch (default: 100)
            
        Returns:
            List of email dictionaries with 'id' field
            
        Raises:
            Exception: If service not authenticated or fetch fails
        """
        if self.auth_mode == 'oauth':
            return self._fetch_emails_oauth(max_results)
        elif self.auth_mode == 'app_password':
            return self._fetch_emails_imap(max_results)
        else:
            raise Exception("Not authenticated. Call authenticate() first.")
    
    def fetch_emails_raw(self, max_results: int = 100) -> List[str]:
        """
        Fetch emails and return raw email text (PROFILE-INDEPENDENT MODE).
        
        This method fetches emails and extracts their content WITHOUT any
        profile-based processing. Used for inbox scanning mode.
        
        Args:
            max_results: Maximum number of emails to fetch (default: 100)
            
        Returns:
            List of raw email text strings (subject + body)
            
        Raises:
            Exception: If not authenticated or fetch fails
        """
        try:
            # Fetch email list
            messages = self.fetch_emails(max_results=max_results)
            
            if not messages:
                logger.info("No emails found")
                return []
            
            # Extract content from each email
            logger.info(f"Extracting content from {len(messages)} emails")
            emails = []
            
            for i, message in enumerate(messages):
                try:
                    message_id = message.get('id')
                    content = self.extract_email_content(message_id)
                    
                    # Format as email text (subject + body)
                    email_text = f"Subject: {content['subject']}\n\n{content['body']}"
                    emails.append(email_text)
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"Processed {i + 1}/{len(messages)} emails")
                        
                except Exception as e:
                    logger.warning(f"Failed to extract email {message_id}: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(emails)} raw emails")
            return emails
            
        except Exception as e:
            logger.error(f"Email fetch error: {str(e)}")
            raise Exception(f"Failed to fetch raw emails: {str(e)}")
    
    def _fetch_emails_oauth(self, max_results: int) -> List[Dict[str, Any]]:
        """Fetch emails using Gmail API (OAuth mode)."""
        if not self.service:
            raise Exception("Gmail service not authenticated.")
        
        try:
            logger.info(f"Fetching last {max_results} emails via Gmail API")
            
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['INBOX'],
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                logger.info("No messages found in inbox")
                return []
            
            logger.info(f"Successfully fetched {len(messages)} email IDs")
            return messages
            
        except HttpError as e:
            error_details = e.error_details if hasattr(e, 'error_details') else str(e)
            logger.error(f"Gmail API fetch error: {error_details}")
            
            if e.resp.status == 429:
                raise Exception(
                    "Gmail API quota exceeded. Please try again later or "
                    "reduce the number of emails to fetch."
                )
            elif e.resp.status == 403:
                raise Exception(
                    "Permission denied: Unable to access Gmail inbox. "
                    "Please check your API permissions and scopes."
                )
            else:
                raise Exception(f"Failed to fetch emails: {error_details}")
                
        except Exception as e:
            logger.error(f"Unexpected error fetching emails: {str(e)}")
            raise Exception(f"Failed to fetch emails from Gmail: {str(e)}")
    
    def _fetch_emails_imap(self, max_results: int) -> List[Dict[str, Any]]:
        """Fetch emails using IMAP (App Password mode)."""
        if not self.imap_connection:
            raise Exception("IMAP connection not established.")
        
        try:
            logger.info(f"Fetching last {max_results} emails via IMAP")
            
            # Select inbox
            self.imap_connection.select('INBOX', readonly=True)
            
            # Search for all emails
            status, message_ids = self.imap_connection.search(None, 'ALL')
            
            if status != 'OK':
                raise Exception(f"IMAP search failed: {status}")
            
            # Get list of message IDs
            id_list = message_ids[0].split()
            
            if not id_list:
                logger.info("No messages found in inbox")
                return []
            
            # Get last N messages (most recent)
            recent_ids = id_list[-max_results:] if len(id_list) > max_results else id_list
            
            # Format as list of dicts with 'id' field (to match OAuth format)
            messages = [{'id': msg_id.decode('utf-8')} for msg_id in recent_ids]
            
            logger.info(f"Successfully fetched {len(messages)} email IDs via IMAP")
            return messages
            
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP fetch error: {str(e)}")
            raise Exception(f"Failed to fetch emails via IMAP: {str(e)}")
            
        except Exception as e:
            logger.error(f"Unexpected IMAP error: {str(e)}")
            raise Exception(f"Failed to fetch emails from Gmail: {str(e)}")
    
    def extract_email_content(self, message_id: str) -> Dict[str, str]:
        """
        Extract subject and body content from a Gmail message.
        
        Supports both OAuth (Gmail API) and App Password (IMAP) modes.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Dictionary with 'subject', 'body', and 'snippet' fields
            
        Raises:
            Exception: If service not authenticated or extraction fails
        """
        if self.auth_mode == 'oauth':
            return self._extract_content_oauth(message_id)
        elif self.auth_mode == 'app_password':
            return self._extract_content_imap(message_id)
        else:
            raise Exception("Not authenticated. Call authenticate() first.")
    
    def _extract_content_oauth(self, message_id: str) -> Dict[str, str]:
        """Extract email content using Gmail API (OAuth mode)."""
        if not self.service:
            raise Exception("Gmail service not authenticated.")
        
        try:
            # Fetch full message details
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = message.get('payload', {}).get('headers', [])
            subject = next(
                (h['value'] for h in headers if h['name'].lower() == 'subject'),
                'No Subject'
            )
            
            # Extract body
            raw_body = self._extract_body_from_payload(message.get('payload', {}))
            
            # Get snippet as fallback
            snippet = message.get('snippet', '')
            
            # ─────────────────────────────────────────────────────────────────
            # PREPROCESSING: Clean HTML/CSS/metadata before returning
            # ─────────────────────────────────────────────────────────────────
            body_to_clean = raw_body if raw_body else snippet
            cleaned_body = clean_email_payload(body_to_clean)
            
            result = {
                'subject': subject,
                'body': cleaned_body,
                'snippet': snippet[:200]  # Keep short snippet for reference
            }
            
            logger.debug(f"Extracted and cleaned content from message {message_id}: subject='{subject[:50]}...'")
            return result
            
        except HttpError as e:
            error_details = e.error_details if hasattr(e, 'error_details') else str(e)
            logger.error(f"Gmail API extraction error for message {message_id}: {error_details}")
            
            if e.resp.status == 404:
                raise Exception(f"Message not found: {message_id}")
            else:
                raise Exception(f"Failed to extract email content: {error_details}")
                
        except Exception as e:
            logger.error(f"Unexpected error extracting email {message_id}: {str(e)}")
            raise Exception(f"Failed to extract email content: {str(e)}")
    
    def _extract_content_imap(self, message_id: str) -> Dict[str, str]:
        """Extract email content using IMAP (App Password mode)."""
        if not self.imap_connection:
            raise Exception("IMAP connection not established.")
        
        try:
            # Fetch email by ID
            status, msg_data = self.imap_connection.fetch(message_id, '(RFC822)')
            
            if status != 'OK':
                raise Exception(f"IMAP fetch failed: {status}")
            
            # Parse email
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Extract subject
            subject = email_message.get('Subject', 'No Subject')
            
            # Extract body
            raw_body = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get('Content-Disposition', ''))
                    
                    # Skip attachments
                    if 'attachment' in content_disposition:
                        continue
                    
                    # Get text/plain parts
                    if content_type == 'text/plain':
                        try:
                            raw_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                        except:
                            continue
                    
                    # Fallback to text/html
                    if content_type == 'text/html' and not raw_body:
                        try:
                            raw_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        except:
                            continue
            else:
                # Non-multipart message
                try:
                    raw_body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    raw_body = str(email_message.get_payload())
            
            # ─────────────────────────────────────────────────────────────────
            # PREPROCESSING: Clean HTML/CSS/metadata before returning
            # ─────────────────────────────────────────────────────────────────
            cleaned_body = clean_email_payload(raw_body)
            
            # Create snippet from cleaned content (first 200 chars)
            snippet = cleaned_body[:200] if cleaned_body else ''
            
            result = {
                'subject': subject,
                'body': cleaned_body,
                'snippet': snippet
            }
            
            logger.debug(f"Extracted and cleaned content from message {message_id}: subject='{subject[:50]}...'")
            return result
            
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP extraction error for message {message_id}: {str(e)}")
            raise Exception(f"Failed to extract email content via IMAP: {str(e)}")
            
        except Exception as e:
            logger.error(f"Unexpected IMAP error extracting email {message_id}: {str(e)}")
            raise Exception(f"Failed to extract email content: {str(e)}")
    
    def _extract_body_from_payload(self, payload: Dict[str, Any]) -> str:
        """
        Recursively extract email body from message payload.
        
        Handles both simple and multipart MIME messages.
        
        Args:
            payload: Gmail message payload
            
        Returns:
            Decoded email body text
        """
        body_text = ""
        
        # Check if payload has body data
        if 'body' in payload and 'data' in payload['body']:
            body_data = payload['body']['data']
            body_text = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
            return body_text
        
        # Handle multipart messages
        if 'parts' in payload:
            for part in payload['parts']:
                # Prefer text/plain, fallback to text/html
                mime_type = part.get('mimeType', '')
                
                if mime_type == 'text/plain':
                    if 'data' in part.get('body', {}):
                        body_data = part['body']['data']
                        body_text = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                        return body_text
                
                # Recursively check nested parts
                if 'parts' in part:
                    nested_body = self._extract_body_from_payload(part)
                    if nested_body:
                        body_text = nested_body
                        return body_text
                
                # Fallback to HTML if no plain text found
                if mime_type == 'text/html' and not body_text:
                    if 'data' in part.get('body', {}):
                        body_data = part['body']['data']
                        body_text = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
        
        return body_text


class OutlookScanner:
    """
    Outlook email scanner using Microsoft Graph API.
    
    Handles OAuth 2.0 authentication, fetches emails from inbox,
    and extracts email content (subject and body).
    
    Requirements: 10.2, 10.3, 10.6
    """
    
    def __init__(self, credentials: Dict[str, str]):
        """
        Initialize Outlook scanner with Microsoft Graph API credentials.
        
        Args:
            credentials: Dictionary containing OAuth credentials
                - access_token: OAuth 2.0 access token
        """
        self.credentials = credentials
        self.access_token = None
        logger.info("OutlookScanner initialized")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Microsoft Graph API using OAuth 2.0.
        
        Returns:
            bool: True if authentication successful, False otherwise
            
        Raises:
            ValueError: If credentials are missing required fields
            Exception: If authentication fails
        """
        try:
            # Validate required credentials
            if not self.credentials.get('access_token'):
                raise ValueError("Missing required field: access_token")
            
            self.access_token = self.credentials.get('access_token')
            
            # Test authentication by fetching user profile
            import requests
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Successfully authenticated Outlook account: {user_data.get('mail', user_data.get('userPrincipalName'))}")
                return True
            elif response.status_code == 401:
                raise Exception(
                    "Authentication failed: Invalid or expired access token. "
                    "Please regenerate your OAuth token."
                )
            else:
                raise Exception(f"Authentication failed: {response.text}")
                
        except ValueError as e:
            logger.error(f"Credential validation error: {str(e)}")
            raise ValueError(f"Invalid credentials: {str(e)}")
            
        except Exception as e:
            logger.error(f"Outlook authentication error: {str(e)}")
            raise Exception(f"Failed to authenticate with Outlook: {str(e)}")
    
    def fetch_emails(self, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch last N emails from Outlook inbox using Microsoft Graph API.
        
        Args:
            max_results: Maximum number of emails to fetch (default: 100)
            
        Returns:
            List of email dictionaries with 'id' field
            
        Raises:
            Exception: If not authenticated or fetch fails
        """
        if not self.access_token:
            raise Exception("Outlook service not authenticated. Call authenticate() first.")
        
        try:
            import requests
            
            logger.info(f"Fetching last {max_results} emails from Outlook inbox")
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Fetch messages from inbox
            response = requests.get(
                f'https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages?$top={max_results}&$select=id',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get('value', [])
                logger.info(f"Successfully fetched {len(messages)} email IDs")
                return messages
            elif response.status_code == 429:
                raise Exception(
                    "Microsoft Graph API rate limit exceeded. Please try again later."
                )
            elif response.status_code == 403:
                raise Exception(
                    "Permission denied: Unable to access Outlook inbox. "
                    "Please check your API permissions and scopes."
                )
            else:
                raise Exception(f"Failed to fetch emails: {response.text}")
                
        except Exception as e:
            logger.error(f"Outlook fetch error: {str(e)}")
            raise Exception(f"Failed to fetch emails from Outlook: {str(e)}")
    
    def fetch_emails_raw(self, max_results: int = 100) -> List[str]:
        """
        Fetch emails and return raw email text (PROFILE-INDEPENDENT MODE).
        
        This method fetches emails and extracts their content WITHOUT any
        profile-based processing. Used for inbox scanning mode.
        
        Args:
            max_results: Maximum number of emails to fetch (default: 100)
            
        Returns:
            List of raw email text strings (subject + body)
            
        Raises:
            Exception: If not authenticated or fetch fails
        """
        try:
            # Fetch email list
            messages = self.fetch_emails(max_results=max_results)
            
            if not messages:
                logger.info("No emails found")
                return []
            
            # Extract content from each email
            logger.info(f"Extracting content from {len(messages)} emails")
            emails = []
            
            for i, message in enumerate(messages):
                try:
                    message_id = message.get('id')
                    content = self.extract_email_content(message_id)
                    
                    # Format as email text (subject + body)
                    email_text = f"Subject: {content['subject']}\n\n{content['body']}"
                    emails.append(email_text)
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"Processed {i + 1}/{len(messages)} emails")
                        
                except Exception as e:
                    logger.warning(f"Failed to extract email {message_id}: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(emails)} raw emails")
            return emails
            
        except Exception as e:
            logger.error(f"Email fetch error: {str(e)}")
            raise Exception(f"Failed to fetch raw emails: {str(e)}")
    
    def extract_email_content(self, message_id: str) -> Dict[str, str]:
        """
        Extract subject and body content from an Outlook message.
        
        Args:
            message_id: Outlook message ID
            
        Returns:
            Dictionary with 'subject', 'body', and 'snippet' fields
            
        Raises:
            Exception: If not authenticated or extraction fails
        """
        if not self.access_token:
            raise Exception("Outlook service not authenticated. Call authenticate() first.")
        
        try:
            import requests
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Fetch full message details
            response = requests.get(
                f'https://graph.microsoft.com/v1.0/me/messages/{message_id}?$select=subject,body,bodyPreview',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                message = response.json()
                
                subject = message.get('subject', 'No Subject')
                body_content = message.get('body', {})
                raw_body = body_content.get('content', '')
                snippet = message.get('bodyPreview', '')
                
                # ─────────────────────────────────────────────────────────────────
                # PREPROCESSING: Clean HTML/CSS/metadata before returning
                # ─────────────────────────────────────────────────────────────────
                body_to_clean = raw_body if raw_body else snippet
                cleaned_body = clean_email_payload(body_to_clean)
                
                result = {
                    'subject': subject,
                    'body': cleaned_body,
                    'snippet': snippet[:200]  # Keep short snippet for reference
                }
                
                logger.debug(f"Extracted and cleaned content from message {message_id}: subject='{subject[:50]}...'")
                return result
                
            elif response.status_code == 404:
                raise Exception(f"Message not found: {message_id}")
            else:
                raise Exception(f"Failed to extract email content: {response.text}")
                
        except Exception as e:
            logger.error(f"Outlook extraction error for message {message_id}: {str(e)}")
            raise Exception(f"Failed to extract email content: {str(e)}")


class EmailProcessor:
    """
    Process emails from Gmail or Outlook through the scoring engine.
    
    Coordinates email fetching, content extraction, and opportunity scoring.
    """
    
    def __init__(self, scanner):
        """
        Initialize email processor with a scanner instance.
        
        Args:
            scanner: GmailScanner or OutlookScanner instance
        """
        self.scanner = scanner
        logger.info(f"EmailProcessor initialized with {type(scanner).__name__}")
    
    def scan_and_process(self, profile: Dict[str, Any], max_emails: int = 100) -> Dict[str, Any]:
        """
        Fetch emails, extract content, and process through scoring engine.
        
        This method coordinates the complete email scanning workflow:
        1. Authenticate with email provider
        2. Fetch email list
        3. Extract content from each email
        4. Format for processing by scoring engine
        
        Args:
            profile: Student profile dictionary
            max_emails: Maximum number of emails to fetch (default: 100)
            
        Returns:
            Dictionary with 'emails' list ready for scoring engine
            Format matches /process-files endpoint input
            
        Raises:
            Exception: If authentication, fetching, or extraction fails
        """
        try:
            # Authenticate
            logger.info("Authenticating with email provider")
            self.scanner.authenticate()
            
            # Fetch email list
            logger.info(f"Fetching up to {max_emails} emails")
            messages = self.scanner.fetch_emails(max_results=max_emails)
            
            if not messages:
                logger.info("No emails found")
                return {'emails': []}
            
            # Extract content from each email
            logger.info(f"Extracting content from {len(messages)} emails")
            emails = []
            
            for i, message in enumerate(messages):
                try:
                    message_id = message.get('id')
                    content = self.scanner.extract_email_content(message_id)
                    
                    # Format as email text (subject + body)
                    email_text = f"Subject: {content['subject']}\n\n{content['body']}"
                    emails.append(email_text)
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"Processed {i + 1}/{len(messages)} emails")
                        
                except Exception as e:
                    logger.warning(f"Failed to extract email {message_id}: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(emails)} emails")
            
            return {
                'emails': emails,
                'total_fetched': len(messages),
                'successfully_extracted': len(emails)
            }
            
        except Exception as e:
            logger.error(f"Email processing error: {str(e)}")
            raise Exception(f"Failed to scan and process emails: {str(e)}")
