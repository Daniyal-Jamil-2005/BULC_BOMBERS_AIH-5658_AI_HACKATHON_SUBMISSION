# Inbox_COPILOT — Opportunity Inbox Copilot


---

## QUICK START (2 commands)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Then open `frontend/index.html` in your browser.

---

## DATABASE SETUP

### MySQL Configuration
The application uses MySQL for structured data storage (user profiles, scan history, bookmarks, checklists).

**Environment Variables** (already configured in `.env`):
```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=inbox_copilot_db
```

**Create the database**:
```sql
CREATE DATABASE inbox_copilot_db;
```

**Run migrations** (creates all tables):
```bash
python -m database.migrations
```

### Neo4j Configuration
The application uses Neo4j for graph relationships (skills, opportunities, students).

**Environment Variables** (already configured in `.env`):
```
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

Neo4j AuraDB (cloud) is recommended for easy setup: https://neo4j.com/cloud/aura/

---

## GMAIL API SETUP

The application supports scanning Gmail inboxes for opportunities using the Gmail API.

### Prerequisites
1. **Google Cloud Project**: Create a project at https://console.cloud.google.com/
2. **Enable Gmail API**: In your project, enable the Gmail API
3. **OAuth 2.0 Credentials**: Create OAuth 2.0 credentials (Desktop app type)
4. **Download credentials**: Download the credentials JSON file

### Configuration Steps

1. **Place credentials file**:
   ```bash
   # Save your OAuth credentials as:
   backend/credentials.json
   ```

2. **First-time authentication**:
   - When you first run the Gmail scanner, it will open a browser window
   - Sign in with your Google account
   - Grant the requested permissions
   - A `token.json` file will be created automatically for future use

3. **Required OAuth Scopes**:
   - `https://www.googleapis.com/auth/gmail.readonly` - Read emails from Gmail

### Security Notes
- Never commit `credentials.json` or `token.json` to version control
- These files are already in `.gitignore`
- Tokens expire after a period of inactivity and will require re-authentication
- For production use, implement proper token refresh logic

### Testing Gmail Integration
```python
from email_scanner import GmailScanner

# Initialize scanner
scanner = GmailScanner(credentials_path='credentials.json')

# Authenticate (opens browser on first run)
scanner.authenticate()

# Fetch last 100 emails
emails = scanner.fetch_emails(max_results=100)
```

---

## OUTLOOK API SETUP

The application supports scanning Outlook/Microsoft 365 inboxes for opportunities using the Microsoft Graph API.

### Prerequisites
1. **Microsoft Azure Account**: Create an account at https://portal.azure.com/
2. **App Registration**: Register a new application in Azure Active Directory
3. **API Permissions**: Configure Microsoft Graph API permissions
4. **Client Secret**: Generate a client secret for authentication

### Configuration Steps

1. **Register Application in Azure Portal**:
   - Navigate to Azure Active Directory > App registrations
   - Click "New registration"
   - Name: "Inbox Copilot" (or your preferred name)
   - Supported account types: "Accounts in any organizational directory and personal Microsoft accounts"
   - Redirect URI: Leave blank for now (or use http://localhost for desktop apps)
   - Click "Register"

2. **Configure API Permissions**:
   - In your app registration, go to "API permissions"
   - Click "Add a permission" > "Microsoft Graph" > "Delegated permissions"
   - Add the following permissions:
     - `Mail.Read` - Read user mail
     - `User.Read` - Sign in and read user profile
   - Click "Add permissions"
   - (Optional) Click "Grant admin consent" if you have admin rights

3. **Create Client Secret**:
   - Go to "Certificates & secrets"
   - Click "New client secret"
   - Description: "Inbox Copilot Secret"
   - Expires: Choose appropriate duration (6 months, 12 months, or 24 months)
   - Click "Add"
   - **IMPORTANT**: Copy the secret value immediately - it won't be shown again!

4. **Configure Environment Variables**:
   Add to your `.env` file:
   ```
   OUTLOOK_CLIENT_ID=your_application_client_id
   OUTLOOK_CLIENT_SECRET=your_client_secret_value
   OUTLOOK_TENANT_ID=common  # Use "common" for multi-tenant, or your specific tenant ID
   ```

   Find these values in Azure Portal:
   - **Client ID**: Overview page > Application (client) ID
   - **Tenant ID**: Overview page > Directory (tenant) ID (or use "common")
   - **Client Secret**: The value you copied in step 3

### Authentication Flow

The application uses OAuth 2.0 authorization code flow with MSAL (Microsoft Authentication Library):

1. **First-time authentication**:
   - User provides their Outlook email address
   - Application redirects to Microsoft login page
   - User signs in and grants permissions
   - Application receives access token and refresh token

2. **Token Management**:
   - Access tokens are valid for 1 hour
   - Refresh tokens are used to obtain new access tokens automatically
   - Tokens are stored securely in the database (encrypted)

### Security Notes
- Never commit client secrets to version control
- Store secrets in `.env` file (already in `.gitignore`)
- Use environment variables for production deployments
- Implement proper token refresh logic for long-running applications
- Consider using Azure Key Vault for production secret management

### Testing Outlook Integration
```python
from email_scanner import OutlookScanner

# Initialize scanner with credentials
credentials = {
    'client_id': 'your_client_id',
    'client_secret': 'your_client_secret',
    'tenant_id': 'common'
}
scanner = OutlookScanner(credentials=credentials)

# Authenticate (opens browser for OAuth flow)
scanner.authenticate()

# Fetch last 100 emails
emails = scanner.fetch_emails(max_results=100)
```

### Troubleshooting

**Error: "AADSTS50011: The reply URL specified in the request does not match"**
- Solution: Add the redirect URI to your app registration in Azure Portal

**Error: "Insufficient privileges to complete the operation"**
- Solution: Ensure Mail.Read permission is granted and admin consent is provided

**Error: "Invalid client secret"**
- Solution: Generate a new client secret and update your `.env` file

**Token Refresh Issues**:
- Refresh tokens expire after 90 days of inactivity
- Users will need to re-authenticate if refresh token expires

---

## PROJECT STRUCTURE

```
project/
├── backend/
│   ├── main.py          ← FastAPI app, all endpoints
│   ├── engine.py        ← Deterministic scoring engine (105 pts, 6 dimensions)
│   ├── llm_client.py    ← Groq API client (llama-3.3-70b-versatile)
│   ├── models.py        ← Pydantic schemas
│   ├── test_backend.py  ← HTTP-level test runner
│   └── requirements.txt
├── frontend/
│   └── index.html       ← Complete SPA (zero build step, open directly)
├── start.py             ← One-click launcher
└── README.md
```

---

## BACKEND — API ENDPOINTS

| Method | Path          | Description                              |
|--------|---------------|------------------------------------------|
| GET    | /             | Root + endpoint map                      |
| GET    | /health       | Health check                             |
| GET    | /sample-data  | 15 sample emails + demo student profile  |
| POST   | /process      | **Main pipeline** — full scan & rank     |
| GET    | /docs         | Swagger UI (auto-generated)              |

### POST /process — Request body
```json
{
  "profile": {
    "degree": "BSCS",
    "semester": 6,
    "cgpa": 3.4,
    "skills": ["Python", "Machine Learning", "AWS"],
    "preferred_opportunity_types": ["internship", "hackathon", "scholarship"],
    "location_preference": "Lahore",
    "financial_need": true
  },
  "emails": [
    "Subject: ...\nBody...",
    "---",
    "Subject: ...\nBody..."
  ]
}
```

---

## SCORING ENGINE (105 pts max — fully deterministic, zero LLM)

| Dimension        | Max Pts | Logic                                                 |
|------------------|---------|-------------------------------------------------------|
| Skill Alignment  | 40      | % of student skills found in email body/eligibility   |
| Urgency          | 30      | CRITICAL ≤2d / HIGH ≤7d / MEDIUM ≤14d / LOW ≤30d    |
| Type Match       | 15      | Exact match=15, partial=8 vs preferred_types          |
| Location         | 10      | Remote=10, city match=8, national=5, international=0  |
| Financial Bonus  | 5       | +5 if scholarship/grant AND student has financial need |
| Completeness     | 5       | All key fields present (deadline, link, eligibility)  |

### Hard Disqualifiers (applied before scoring — INELIGIBLE)
1. CGPA too low (student CGPA < email min_cgpa)
2. Degree mismatch (email restricts to specific degrees)
3. Missing mandatory language/certification (e.g. N5 Japanese, IELTS 7.0)
4. Graduation year restriction (student won't graduate in time)

---

## FRONTEND — 4 VIEWS

| View             | Description                                          |
|------------------|------------------------------------------------------|
| SCAN_PROCESS     | Input form: student profile + email paste area       |
| SYSTEM_INTEL     | Ranked opportunity cards with expandable checklists  |
| ELIMINATED_NOISE | Log of all discarded/non-opportunity emails          |
| USER_PROFILE     | Visual summary of the active student profile         |

Each opportunity card includes:
- Urgency badge (CRITICAL / HIGH / MEDIUM / LOW)
- 6-dimension mini score bars
- Expandable checklist + score reasoning
- AUDIT_TRAIL modal with full logic trace table
- Direct APPLY_NOW link

---

## RUNNING THE TEST SUITE

With the backend running:
```bash
cd backend
python test_backend.py
```

Health-only check:
```bash
python test_backend.py --health
```

---

## API KEY

Groq API key is pre-configured in `backend/llm_client.py`.
Model: `llama-3.3-70b-versatile` at temperature=0 for deterministic extraction.

To update: edit `GROQ_API_KEY` in `backend/llm_client.py`.
