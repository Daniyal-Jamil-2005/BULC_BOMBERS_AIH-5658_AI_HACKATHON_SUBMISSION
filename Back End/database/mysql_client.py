"""
MySQL Database Client for Inbox Copilot
Handles all MySQL database operations with proper error handling
"""

import mysql.connector
from typing import Optional, List, Dict, Any
import os
import json
import uuid
import bcrypt
from datetime import datetime

class MySQLClient:
    def __init__(self):
        self.config = {
            'host': os.getenv("MYSQL_HOST", "localhost"),
            'port': int(os.getenv("MYSQL_PORT", "3306")),
            'user': os.getenv("MYSQL_USER"),
            'password': os.getenv("MYSQL_PASSWORD"),
            'database': os.getenv("MYSQL_DATABASE")
        }
        self.connection = None

    # ─── AUTH OPERATIONS ───────────────────────────────────────────────────

    def signup(self, name: str, email: str, password: str) -> Dict[str, Any]:
        """Create a new user. Raises ValueError if email already exists."""
        # Check if email already registered
        existing = self._execute_query(
            "SELECT id FROM users WHERE email = %s", (email,), fetch_one=True
        )
        if existing:
            raise ValueError("Email already registered")

        user_id = str(uuid.uuid4())
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        self._execute_query(
            """INSERT INTO users (id, email, name, password_hash)
               VALUES (%s, %s, %s, %s)""",
            (user_id, email, name, password_hash)
        )
        return {"user_id": user_id, "email": email, "name": name}

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Verify credentials. Raises ValueError on bad email/password."""
        user = self._execute_query(
            "SELECT id, email, name, password_hash FROM users WHERE email = %s",
            (email,), fetch_one=True
        )
        if not user:
            raise ValueError("No account found with that email")
        if not user.get("password_hash"):
            raise ValueError("Account has no password set — contact support")
        if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            raise ValueError("Incorrect password")
        return {"user_id": user["id"], "email": user["email"], "name": user.get("name", "")}

    def connect(self):
        """Establish database connection"""
        if not self.connection or not self.connection.is_connected():
            self.connection = mysql.connector.connect(**self.config)
        return self.connection
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
    
    def _execute_query(self, query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False):
        """Execute a query with error handling"""
        try:
            conn = self.connect()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.lastrowid
            
            cursor.close()
            return result
        except mysql.connector.Error as err:
            raise Exception(f"Database error: {err}")
    
    # ─── USER PROFILE OPERATIONS ───────────────────────────────────────────
    
    def save_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update user profile"""
        query = """
            INSERT INTO users (id, email, degree, semester, cgpa, skills, 
                             preferred_opportunity_types, location_preference, 
                             financial_need, total_semesters)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                degree = VALUES(degree),
                semester = VALUES(semester),
                cgpa = VALUES(cgpa),
                skills = VALUES(skills),
                preferred_opportunity_types = VALUES(preferred_opportunity_types),
                location_preference = VALUES(location_preference),
                financial_need = VALUES(financial_need),
                total_semesters = VALUES(total_semesters)
        """
        
        params = (
            user_id,
            profile_data.get('email', f'{user_id}@example.com'),
            profile_data.get('degree'),
            profile_data.get('semester'),
            profile_data.get('cgpa'),
            json.dumps(profile_data.get('skills', [])),
            json.dumps(profile_data.get('preferred_opportunity_types', [])),
            profile_data.get('location_preference'),
            profile_data.get('financial_need', False),
            profile_data.get('total_semesters', 8)
        )
        
        self._execute_query(query, params)
        return {'user_id': user_id, 'status': 'saved'}
    
    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user profile by ID"""
        query = "SELECT * FROM users WHERE id = %s"
        result = self._execute_query(query, (user_id,), fetch_one=True)
        
        if result:
            # Parse JSON fields
            result['skills'] = json.loads(result['skills']) if result.get('skills') else []
            result['preferred_opportunity_types'] = json.loads(result['preferred_opportunity_types']) if result.get('preferred_opportunity_types') else []
        
        return result
    
    # ─── SCAN HISTORY OPERATIONS ───────────────────────────────────────────
    
    def save_scan_history(self, user_id: str, scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save scan results to history"""
        scan_id = str(uuid.uuid4())
        query = """
            INSERT INTO scan_history (id, user_id, ranked_count, discarded_count, 
                                    failed_count, results)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        params = (
            scan_id,
            user_id,
            scan_data.get('ranked_count', 0),
            scan_data.get('discarded_count', 0),
            scan_data.get('failed_count', 0),
            json.dumps(scan_data.get('results', {}))
        )
        
        self._execute_query(query, params)
        return {'scan_id': scan_id, 'status': 'saved'}
    
    def get_scan_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve user's scan history"""
        query = """
            SELECT * FROM scan_history 
            WHERE user_id = %s 
            ORDER BY scanned_at DESC 
            LIMIT %s
        """
        results = self._execute_query(query, (user_id, limit), fetch_all=True)
        
        # Parse JSON results field
        for result in results:
            result['results'] = json.loads(result['results']) if result.get('results') else {}
        
        return results
    
    # ─── BOOKMARK OPERATIONS ───────────────────────────────────────────────
    
    def save_bookmark(self, user_id: str, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Bookmark an opportunity"""
        bookmark_id = str(uuid.uuid4())
        query = """
            INSERT INTO saved_opportunities (id, user_id, opportunity_id, title, 
                                           org, type, deadline_iso, score, opportunity_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                org = VALUES(org),
                type = VALUES(type),
                deadline_iso = VALUES(deadline_iso),
                score = VALUES(score),
                opportunity_data = VALUES(opportunity_data)
        """
        
        params = (
            bookmark_id,
            user_id,
            opportunity_data.get('id', str(uuid.uuid4())),
            opportunity_data.get('title'),
            opportunity_data.get('org'),
            opportunity_data.get('type'),
            opportunity_data.get('deadline_iso'),
            opportunity_data.get('score'),
            json.dumps(opportunity_data)
        )
        
        self._execute_query(query, params)
        return {'bookmark_id': bookmark_id, 'status': 'saved'}
    
    def remove_bookmark(self, user_id: str, opportunity_id: str) -> bool:
        """Remove a bookmark"""
        query = "DELETE FROM saved_opportunities WHERE user_id = %s AND opportunity_id = %s"
        self._execute_query(query, (user_id, opportunity_id))
        return True
    
    def get_bookmarks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all bookmarked opportunities"""
        query = """
            SELECT * FROM saved_opportunities 
            WHERE user_id = %s 
            ORDER BY saved_at DESC
        """
        results = self._execute_query(query, (user_id,), fetch_all=True)
        
        # Parse JSON opportunity_data field
        for result in results:
            result['opportunity_data'] = json.loads(result['opportunity_data']) if result.get('opportunity_data') else {}
        
        return results
    
    # ─── CHECKLIST OPERATIONS ──────────────────────────────────────────────
    
    def save_checklist_item(self, user_id: str, opportunity_id: str, 
                           task: str, done: bool) -> Dict[str, Any]:
        """Save checklist item state"""
        checklist_id = str(uuid.uuid4())
        query = """
            INSERT INTO checklists (id, user_id, opportunity_id, task, done, completed_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                done = VALUES(done),
                completed_at = VALUES(completed_at)
        """
        
        completed_at = datetime.now() if done else None
        params = (checklist_id, user_id, opportunity_id, task, done, completed_at)
        
        self._execute_query(query, params)
        return {'checklist_id': checklist_id, 'status': 'saved'}
    
    def get_checklist(self, user_id: str, opportunity_id: str) -> List[Dict[str, Any]]:
        """Get checklist for an opportunity"""
        query = """
            SELECT * FROM checklists 
            WHERE user_id = %s AND opportunity_id = %s 
            ORDER BY priority DESC, id
        """
        return self._execute_query(query, (user_id, opportunity_id), fetch_all=True)
    
    # ─── OAUTH TOKEN OPERATIONS ────────────────────────────────────────────
    
    def save_oauth_token(self, user_id: str, provider: str, 
                        token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save encrypted OAuth tokens"""
        token_id = str(uuid.uuid4())
        query = """
            INSERT INTO oauth_tokens (id, user_id, provider, access_token, 
                                    refresh_token, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                access_token = VALUES(access_token),
                refresh_token = VALUES(refresh_token),
                expires_at = VALUES(expires_at)
        """
        
        params = (
            token_id,
            user_id,
            provider,
            token_data.get('access_token'),
            token_data.get('refresh_token'),
            token_data.get('expires_at')
        )
        
        self._execute_query(query, params)
        return {'token_id': token_id, 'status': 'saved'}
    
    def get_oauth_token(self, user_id: str, provider: str) -> Optional[Dict[str, Any]]:
        """Retrieve OAuth tokens"""
        query = """
            SELECT * FROM oauth_tokens 
            WHERE user_id = %s AND provider = %s
        """
        return self._execute_query(query, (user_id, provider), fetch_one=True)
    
    # ─── EMAIL CREDENTIALS OPERATIONS ──────────────────────────────────────
    
    def save_email_credentials(self, user_id: str, provider: str,
                              email_address: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Save email credentials (app password) for a user+provider pair."""
        credential_id = str(uuid.uuid4())
        query = """
            INSERT INTO email_credentials (id, user_id, provider, email_address, credentials)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                email_address = VALUES(email_address),
                credentials = VALUES(credentials),
                updated_at = CURRENT_TIMESTAMP
        """
        self._execute_query(query, (
            credential_id, user_id, provider, email_address,
            json.dumps(credentials)
        ))
        return {'credential_id': credential_id, 'status': 'saved'}

    def get_email_credentials(self, user_id: str, provider: str) -> Optional[Dict[str, Any]]:
        """Retrieve saved email credentials for a user+provider pair."""
        result = self._execute_query(
            "SELECT * FROM email_credentials WHERE user_id = %s AND provider = %s",
            (user_id, provider), fetch_one=True
        )
        if not result:
            return None
        try:
            creds = result['credentials']
            if isinstance(creds, str):
                creds = json.loads(creds)
            return {
                'id': result['id'],
                'user_id': result['user_id'],
                'provider': result['provider'],
                'email_address': result['email_address'],
                'credentials': creds,
                'created_at': str(result.get('created_at', '')),
                'updated_at': str(result.get('updated_at', '')),
            }
        except Exception:
            return None

    def delete_email_credentials(self, user_id: str, provider: str) -> Dict[str, Any]:
        """Delete saved credentials for a user+provider pair."""
        self._execute_query(
            "DELETE FROM email_credentials WHERE user_id = %s AND provider = %s",
            (user_id, provider)
        )
        return {'status': 'deleted'}
