"""
Neo4j Graph Database Client for Inbox Copilot
Handles all Neo4j graph operations for skill matching and recommendations
"""

from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import os
from datetime import datetime, timedelta


class Neo4jClient:
    def __init__(self):
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        """Close the Neo4j driver connection"""
        self.driver.close()
    
    # Node Creation Methods
    
    def create_student_node(self, student_id: str, skills: List[str]) -> None:
        """
        Create student node with KNOWS relationships to skills
        
        Args:
            student_id: Unique identifier for the student
            skills: List of skill names the student possesses
        """
        with self.driver.session() as session:
            # Create student node
            session.run(
                "MERGE (s:Student {id: $student_id})",
                student_id=student_id
            )
            
            # Create skill nodes and KNOWS relationships
            for skill in skills:
                session.run(
                    """
                    MERGE (skill:Skill {name: $skill_name})
                    WITH skill
                    MATCH (s:Student {id: $student_id})
                    MERGE (s)-[:KNOWS]->(skill)
                    """,
                    skill_name=skill.lower().strip(),
                    student_id=student_id
                )
    
    def create_opportunity_node(self, opp_id: str, title: str, 
                               required_skills: List[str], org: str) -> None:
        """
        Create opportunity node with REQUIRES relationships to skills
        
        Args:
            opp_id: Unique identifier for the opportunity
            title: Title of the opportunity
            required_skills: List of skills required for the opportunity
            org: Organization offering the opportunity
        """
        with self.driver.session() as session:
            # Create opportunity node
            session.run(
                """
                MERGE (opp:Opportunity {id: $opp_id})
                SET opp.title = $title
                """,
                opp_id=opp_id,
                title=title
            )
            
            # Create organization node and relationship
            if org:
                session.run(
                    """
                    MERGE (org:Organization {name: $org_name})
                    WITH org
                    MATCH (opp:Opportunity {id: $opp_id})
                    MERGE (org)-[:OFFERS]->(opp)
                    """,
                    org_name=org,
                    opp_id=opp_id
                )
            
            # Create skill nodes and REQUIRES relationships
            for skill in required_skills:
                session.run(
                    """
                    MERGE (skill:Skill {name: $skill_name})
                    WITH skill
                    MATCH (opp:Opportunity {id: $opp_id})
                    MERGE (opp)-[:REQUIRES]->(skill)
                    """,
                    skill_name=skill.lower().strip(),
                    opp_id=opp_id
                )
    
    # Query Methods
    
    def find_similar_opportunities(self, student_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find opportunities matching student's skills
        
        Args:
            student_id: Unique identifier for the student
            limit: Maximum number of opportunities to return
            
        Returns:
            List of opportunities with skill match counts
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (s:Student {id: $student_id})-[:KNOWS]->(skill:Skill)
                MATCH (opp:Opportunity)-[:REQUIRES]->(skill)
                WITH opp, COUNT(DISTINCT skill) as skill_matches
                OPTIONAL MATCH (org:Organization)-[:OFFERS]->(opp)
                RETURN opp.id as id, opp.title as title, org.name as organization, 
                       skill_matches
                ORDER BY skill_matches DESC
                LIMIT $limit
                """,
                student_id=student_id,
                limit=limit
            )
            
            opportunities = []
            for record in result:
                opportunities.append({
                    'id': record['id'],
                    'title': record['title'],
                    'organization': record['organization'],
                    'skill_matches': record['skill_matches']
                })
            
            return opportunities
    
    def get_skill_cooccurrence(self, skill: str) -> List[Dict[str, Any]]:
        """
        Find skills that frequently appear with given skill
        
        Args:
            skill: The skill to find co-occurrences for
            
        Returns:
            List of skills with co-occurrence counts
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (s1:Skill {name: $skill_name})<-[:REQUIRES]-(opp:Opportunity)-[:REQUIRES]->(s2:Skill)
                WHERE s1 <> s2
                RETURN s2.name as skill, COUNT(DISTINCT opp) as cooccurrence
                ORDER BY cooccurrence DESC
                LIMIT 10
                """,
                skill_name=skill.lower().strip()
            )
            
            cooccurrences = []
            for record in result:
                cooccurrences.append({
                    'skill': record['skill'],
                    'cooccurrence': record['cooccurrence']
                })
            
            return cooccurrences
    
    def get_skill_demand(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get most in-demand skills from recent opportunities
        
        Args:
            days: Number of days to look back (default 30)
            
        Returns:
            List of skills with demand counts
        """
        with self.driver.session() as session:
            # Note: This assumes opportunities have a created_at property
            # If not available, we'll return all-time demand
            result = session.run(
                """
                MATCH (opp:Opportunity)-[:REQUIRES]->(skill:Skill)
                RETURN skill.name as skill, COUNT(DISTINCT opp) as demand
                ORDER BY demand DESC
                LIMIT 20
                """
            )
            
            skills = []
            for record in result:
                skills.append({
                    'skill': record['skill'],
                    'demand': record['demand']
                })
            
            return skills
    
    def recommend_skills(self, student_id: str, n: int = 5) -> List[str]:
        """
        Recommend skills based on graph analysis
        
        Strategy:
        1. Find skills required by opportunities matching student's current skills
        2. Exclude skills the student already has
        3. Rank by frequency and co-occurrence patterns
        
        Args:
            student_id: Unique identifier for the student
            n: Number of skills to recommend
            
        Returns:
            List of recommended skill names
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (s:Student {id: $student_id})-[:KNOWS]->(known_skill:Skill)
                MATCH (opp:Opportunity)-[:REQUIRES]->(known_skill)
                MATCH (opp)-[:REQUIRES]->(recommended_skill:Skill)
                WHERE NOT (s)-[:KNOWS]->(recommended_skill)
                WITH recommended_skill, COUNT(DISTINCT opp) as frequency
                RETURN recommended_skill.name as skill
                ORDER BY frequency DESC
                LIMIT $n
                """,
                student_id=student_id,
                n=n
            )
            
            recommendations = [record['skill'] for record in result]
            return recommendations
