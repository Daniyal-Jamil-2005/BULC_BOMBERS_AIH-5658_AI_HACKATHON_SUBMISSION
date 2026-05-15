# Inbox Copilot

An AI-powered email intelligence tool designed to scan, categorize, and prioritize high-value opportunities directly from your inbox. 

Built during a 2026 hackathon, this copilot uses advanced LLMs to filter through the noise, extracting actionable leads, internships, and professional opportunities. It transforms a cluttered inbox into a streamlined feed of what actually matters, complete with deep analytics and skill gap assessments.

## 🚀 Key Features

- **Automated Opportunity Detection**: Identifies internships, job leads, and collaboration requests using agentic AI.
- **Intelligent Matching & Skill Gap Analysis**: Compares incoming job descriptions against your profile, scoring matches and highlighting missing skills required for the role.
- **Context-Aware Categorization**: Sorts incoming mail based on priority, relevance, and detected deadlines.
- **Beautiful React Dashboard**: A rich, interactive front-end featuring Analytics Dashboards, Keyword Heatmaps, and Skill Gap visualizations.
- **Comprehensive Reporting**: Generates downloadable PDF reports and integrates with a multi-page professional Power BI dashboard for granular metrics and historical tracking.
- **Minimalist Architecture**: Optimized for speed, utilizing a robust FastAPI backend supported by MySQL for structured data and Neo4j for relationship mapping.
- **Seamless Integration**: Designed to sit on top of your existing mail flow to provide real-time assistance.

## 🛠️ Technology Stack

**Frontend:**
- React (Create React App)
- CSS (Custom styling, responsive dashboards, modern UI)

**Backend:**
- Python (FastAPI)
- Language Models (LLMs) for classification and extraction
- Machine Learning (scikit-learn) for heuristic matching models

**Databases:**
- **MySQL**: Relational data storage (email metadata, auth, etc.)
- **Neo4j**: Graph database for mapping entity relationships (skills, jobs, user profiles)

**Analytics:**
- Power BI (Advanced data visualization)
- Python PDF Generation (Automated reports)

## 📂 Project Structure

- `/Front End`: Contains the React web application, UI components, and API integration utilities.
- `/Back End`: Contains the FastAPI server, LLM agents, database schemas/migrations, and ML models.
- `/Misc`: Contains architecture diagrams, screenshots, and the Power BI (`.pbix`) report template.

## 👥 Team
Built by **Daniyal, Aymal, and Muaaz** 
