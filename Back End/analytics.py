"""
IDS (Integrated Data Science) Analytics Module

This module provides data science capabilities using pandas and numpy for opportunity analysis.
It includes three main classes:
- OpportunityAnalytics: Analyzes opportunity data and computes statistics
- HistoricalAnalytics: Tracks trends over time using JSONL storage
- CorpusStatistics: Analyzes email corpus characteristics

Requirements: 3.1, 3.2, 5.1, 6.1
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import json
from pathlib import Path
from models import RankedOpportunity


class OpportunityAnalytics:
    """
    Analyzes opportunity data using pandas DataFrames.
    
    Provides descriptive statistics, distribution analysis, and skill gap identification
    for a set of ranked opportunities.
    
    Requirements: 3.1, 3.2, 3.3, 3.4, 4.1-4.4
    """
    
    def __init__(self, opportunities: List[RankedOpportunity]):
        """
        Initialize analytics with a list of ranked opportunities.
        
        Args:
            opportunities: List of RankedOpportunity objects to analyze
        """
        self.opportunities = opportunities
        self.df = self._build_dataframe(opportunities)
    
    def _build_dataframe(self, opportunities: List[RankedOpportunity]) -> pd.DataFrame:
        """
        Convert opportunities to pandas DataFrame.
        
        Extracts key fields from RankedOpportunity objects into a structured DataFrame
        for efficient analysis.
        
        Args:
            opportunities: List of RankedOpportunity objects
            
        Returns:
            DataFrame with columns: id, title, org, type, score, urgency_badge, deadline_iso
            
        Validates: Property 2 - Analytics DataFrame Construction
        """
        if not opportunities:
            return pd.DataFrame()
        
        data = []
        for opp in opportunities:
            data.append({
                'id': opp.id,
                'title': opp.title,
                'org': opp.org,
                'type': opp.type,
                'score': opp.score_breakdown.total,
                'urgency_badge': opp.urgency_badge,
                'deadline_iso': opp.deadline_iso
            })
        
        return pd.DataFrame(data)
    
    def compute_descriptive_stats(self) -> Dict[str, Any]:
        """
        Compute descriptive statistics for opportunity scores.
        
        Calculates mean, standard deviation, and percentiles (25th, 50th, 75th, 90th)
        for the score distribution.
        
        Returns:
            Dictionary with keys: mean, std, percentiles (dict with 25, 50, 75, 90)
            
        Validates: Property 3 - Descriptive Statistics Validity
        """
        if self.df.empty:
            return {
                'mean': 0.0,
                'std': 0.0,
                'percentiles': {'25': 0.0, '50': 0.0, '75': 0.0, '90': 0.0}
            }
        
        scores = self.df['score']
        
        return {
            'mean': float(scores.mean()),
            'std': float(scores.std()),
            'percentiles': {
                '25': float(scores.quantile(0.25)),
                '50': float(scores.quantile(0.50)),
                '75': float(scores.quantile(0.75)),
                '90': float(scores.quantile(0.90))
            }
        }
    
    def get_type_distribution(self) -> Dict[str, int]:
        """
        Count opportunities by type.
        
        Returns:
            Dictionary mapping opportunity type to count
            
        Validates: Property 4 - Distribution Aggregation Correctness
        """
        if self.df.empty:
            return {}
        
        return self.df['type'].value_counts().to_dict()
    
    def get_urgency_distribution(self) -> Dict[str, int]:
        """
        Count opportunities by urgency level.
        
        Returns:
            Dictionary mapping urgency badge to count
            
        Validates: Property 4 - Distribution Aggregation Correctness
        """
        if self.df.empty:
            return {}
        
        return self.df['urgency_badge'].value_counts().to_dict()
    
    def compute_skill_gaps(self, student_skills: List[str]) -> List[Dict[str, Any]]:
        """
        Identify missing skills and their frequencies across opportunities.
        
        Extracts skills from opportunity eligibility criteria, compares against
        student's current skills, and ranks missing skills by frequency.
        
        Args:
            student_skills: List of skills the student currently has
            
        Returns:
            List of dicts with keys: skill, frequency, missing (always True)
            Sorted by frequency in descending order
            
        Validates: Properties 5, 6, 7 - Skill Extraction, Gap Identification, Ranking
        """
        if self.df.empty or not student_skills:
            return []
        
        # Normalize student skills to lowercase for comparison
        student_skills_lower = {skill.lower().strip() for skill in student_skills}
        
        # Common technical skills to look for
        common_skills = {
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
            'react', 'angular', 'vue', 'node', 'nodejs', 'express', 'django', 'flask',
            'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'redis',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
            'machine learning', 'ml', 'deep learning', 'ai', 'nlp', 'computer vision',
            'data science', 'data analysis', 'pandas', 'numpy', 'tensorflow', 'pytorch',
            'git', 'github', 'ci/cd', 'devops', 'linux', 'bash',
            'html', 'css', 'tailwind', 'bootstrap', 'sass',
            'rest api', 'graphql', 'microservices', 'cloud', 'security',
            'agile', 'scrum', 'testing', 'debugging', 'algorithms'
        }
        
        # Extract skills from opportunities
        all_opportunity_skills = []
        
        for idx, row in self.df.iterrows():
            # Get the original opportunity object to access eligibility
            if idx < len(self.opportunities):
                opp = self.opportunities[idx]
                
                # Extract from eligibility criteria
                if hasattr(opp, 'eligibility') and opp.eligibility:
                    for criterion in opp.eligibility:
                        criterion_lower = criterion.lower()
                        # Look for common skills in the criterion text
                        for skill in common_skills:
                            if skill in criterion_lower:
                                all_opportunity_skills.append(skill)
                
                # Extract from title
                if hasattr(opp, 'title') and opp.title:
                    title_lower = opp.title.lower()
                    for skill in common_skills:
                        if skill in title_lower:
                            all_opportunity_skills.append(skill)
        
        if not all_opportunity_skills:
            return []
        
        # Count skill frequencies using pandas
        skill_series = pd.Series(all_opportunity_skills)
        skill_counts = skill_series.value_counts()
        
        # Identify missing skills (skills in opportunities but not in student profile)
        missing_skills = []
        for skill, frequency in skill_counts.items():
            if skill.lower() not in student_skills_lower:
                missing_skills.append({
                    'skill': skill,
                    'frequency': int(frequency),
                    'missing': True
                })
        
        # Sort by frequency descending
        missing_skills.sort(key=lambda x: x['frequency'], reverse=True)
        
        return missing_skills


class HistoricalAnalytics:
    """
    Tracks opportunity trends over time using JSONL file storage.
    
    Saves scan results with timestamps and computes trend analysis using
    linear regression and percentage change calculations.
    
    Requirements: 5.1, 5.2, 5.3, 5.5
    """
    
    def __init__(self, history_file: str = "scan_history.jsonl"):
        """
        Initialize historical analytics with a JSONL file path.
        
        Args:
            history_file: Path to JSONL file for storing scan history
        """
        self.history_file = Path(history_file)
    
    def save_scan(self, scan_result: Dict[str, Any]) -> None:
        """
        Append scan result to JSONL file with timestamp.
        
        Adds current timestamp and writes the scan result as a JSON line.
        
        Args:
            scan_result: Dictionary containing scan metadata
                        (ranked_count, discarded_count, failed_count, avg_score, types)
                        
        Validates: Property 8 - Scan History Round-Trip Preservation
        """
        scan_result['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Create file if it doesn't exist
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.history_file, 'a') as f:
            f.write(json.dumps(scan_result) + '\n')
    
    def load_history(self, days: int = 30) -> pd.DataFrame:
        """
        Load historical scans from JSONL file.
        
        Reads scan history and filters to the specified number of days.
        
        Args:
            days: Number of days of history to load (default 30)
            
        Returns:
            DataFrame with columns from scan results, filtered by date range
            
        Validates: Property 8 - Scan History Round-Trip Preservation
        """
        if not self.history_file.exists():
            return pd.DataFrame()
        
        records = []
        cutoff_date = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
        
        with open(self.history_file, 'r') as f:
            for line in f:
                record = json.loads(line.strip())
                # Parse timestamp and filter
                timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                if timestamp.timestamp() >= cutoff_date:
                    records.append(record)
        
        return pd.DataFrame(records) if records else pd.DataFrame()
    
    def compute_trends(self) -> Dict[str, Any]:
        """
        Compute linear regression trends on opportunity counts over time.
        
        Uses numpy polyfit to calculate trend line parameters.
        
        Returns:
            Dictionary with keys: slope, intercept, r_squared
            
        Validates: Property 9 - Trend Regression Validity
        """
        df = self.load_history()
        
        if df.empty or len(df) < 2:
            return {
                'slope': 0.0,
                'intercept': 0.0,
                'r_squared': 0.0,
                'insufficient_data': True
            }
        
        # Convert timestamps to numeric values (days since first scan)
        df['timestamp_dt'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp_dt')
        first_date = df['timestamp_dt'].iloc[0]
        df['days_since_start'] = (df['timestamp_dt'] - first_date).dt.total_seconds() / (24 * 60 * 60)
        
        # Perform linear regression
        x = df['days_since_start'].values
        y = df['ranked_count'].values
        
        # Calculate regression using numpy
        coefficients = np.polyfit(x, y, 1)
        slope, intercept = coefficients
        
        # Calculate R-squared
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        
        return {
            'slope': float(slope),
            'intercept': float(intercept),
            'r_squared': float(r_squared),
            'insufficient_data': False
        }
    
    def get_week_over_week_change(self) -> float:
        """
        Calculate percentage change from previous week.
        
        Compares average opportunity count from last 7 days to previous 7 days.
        
        Returns:
            Percentage change (positive = increase, negative = decrease)
            Returns 0.0 if insufficient data
            
        Validates: Property 10 - Percentage Change Calculation
        """
        df = self.load_history(days=14)  # Need 2 weeks of data
        
        if df.empty or len(df) < 2:
            return 0.0
        
        df['timestamp_dt'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp_dt')
        
        # Split into two weeks
        cutoff = datetime.utcnow().timestamp() - (7 * 24 * 60 * 60)
        cutoff_dt = datetime.fromtimestamp(cutoff)
        
        current_week = df[df['timestamp_dt'] >= cutoff_dt]
        previous_week = df[df['timestamp_dt'] < cutoff_dt]
        
        if previous_week.empty or current_week.empty:
            return 0.0
        
        current_avg = current_week['ranked_count'].mean()
        previous_avg = previous_week['ranked_count'].mean()
        
        if previous_avg == 0:
            return 100.0 if current_avg > 0 else 0.0
        
        return float(((current_avg - previous_avg) / previous_avg) * 100)


class CorpusStatistics:
    """
    Analyzes email corpus characteristics.
    
    Computes readability statistics, keyword density, and term frequency
    for a collection of email texts.
    
    Requirements: 6.1, 6.2, 6.3, 6.4
    """
    
    def __init__(self, email_texts: List[str]):
        """
        Initialize corpus statistics with email texts.
        
        Args:
            email_texts: List of email body texts to analyze
        """
        self.emails = email_texts
    
    def compute_readability_stats(self) -> Dict[str, float]:
        """
        Calculate average word count, sentence count, and character length.
        
        Returns:
            Dictionary with keys: avg_word_count, avg_sentence_count, avg_char_length
            
        Validates: Property 11 - Corpus Statistics Consistency
        """
        if not self.emails:
            return {
                'avg_word_count': 0.0,
                'avg_sentence_count': 0.0,
                'avg_char_length': 0.0
            }
        
        word_counts = []
        sentence_counts = []
        char_lengths = []
        
        for email in self.emails:
            # Word count
            words = email.split()
            word_counts.append(len(words))
            
            # Sentence count (approximate by counting sentence-ending punctuation)
            sentences = email.count('.') + email.count('!') + email.count('?')
            sentence_counts.append(max(1, sentences))  # At least 1 sentence
            
            # Character length
            char_lengths.append(len(email))
        
        return {
            'avg_word_count': float(np.mean(word_counts)),
            'avg_sentence_count': float(np.mean(sentence_counts)),
            'avg_char_length': float(np.mean(char_lengths))
        }
    
    def compute_keyword_density(self, keywords: List[str]) -> Dict[str, float]:
        """
        Calculate frequency of specific keywords as a proportion of total words.
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            Dictionary mapping keyword to density (0.0 to 1.0)
            
        Validates: Property 11 - Corpus Statistics Consistency
        """
        if not self.emails or not keywords:
            return {kw: 0.0 for kw in keywords}
        
        # Combine all emails into one corpus
        corpus = ' '.join(self.emails).lower()
        total_words = len(corpus.split())
        
        if total_words == 0:
            return {kw: 0.0 for kw in keywords}
        
        keyword_density = {}
        for keyword in keywords:
            count = corpus.count(keyword.lower())
            keyword_density[keyword] = count / total_words
        
        return keyword_density
    
    def get_top_terms(self, n: int = 20) -> List[tuple]:
        """
        Return most frequent terms excluding stop words.
        
        Args:
            n: Number of top terms to return
            
        Returns:
            List of (term, frequency) tuples sorted by frequency descending
            
        Validates: Property 12 - Frequent Terms Ranking
        """
        if not self.emails:
            return []
        
        # Common English stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each',
            'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
            'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very'
        }
        
        # Combine all emails and tokenize
        corpus = ' '.join(self.emails).lower()
        words = corpus.split()
        
        # Filter out stop words and count frequencies
        word_freq = {}
        for word in words:
            # Remove punctuation
            word = ''.join(c for c in word if c.isalnum())
            if word and word not in stop_words and len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top n
        sorted_terms = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return sorted_terms[:n]
    
    def extract_keywords_from_opportunities(self, opportunities: List[RankedOpportunity], n: int = 30) -> List[Dict[str, Any]]:
        """
        Extract keywords from opportunity titles and descriptions.
        
        Combines opportunity titles, organizations, and types to identify
        the most frequent keywords across all opportunities.
        
        Args:
            opportunities: List of RankedOpportunity objects
            n: Number of top keywords to return
            
        Returns:
            List of dicts with keys: keyword, frequency
            Sorted by frequency in descending order
            
        Requirements: 20.1, 20.2, 20.5
        """
        if not opportunities:
            return []
        
        # Common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each',
            'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
            'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
            'opportunity', 'opportunities', 'application', 'apply', 'deadline'
        }
        
        # Collect all text from opportunities
        all_text = []
        for opp in opportunities:
            if hasattr(opp, 'title') and opp.title:
                all_text.append(opp.title)
            if hasattr(opp, 'org') and opp.org:
                all_text.append(opp.org)
            if hasattr(opp, 'type') and opp.type:
                all_text.append(opp.type)
            if hasattr(opp, 'eligibility') and opp.eligibility:
                all_text.extend(opp.eligibility)
        
        if not all_text:
            return []
        
        # Combine and tokenize
        corpus = ' '.join(all_text).lower()
        words = corpus.split()
        
        # Count word frequencies
        word_freq = {}
        for word in words:
            # Remove punctuation
            word = ''.join(c for c in word if c.isalnum())
            if word and word not in stop_words and len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top n
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:n]
        
        # Format as list of dicts
        return [{'keyword': kw, 'frequency': freq} for kw, freq in sorted_keywords]
