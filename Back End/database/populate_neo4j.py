"""
Neo4j Graph Population Script
Populates Neo4j with initial skill taxonomy and relationships
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import neo4j_client
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from database.neo4j_client import Neo4jClient
from typing import List, Dict


# Common skills taxonomy organized by category
SKILL_TAXONOMY = {
    "Programming Languages": [
        "python", "javascript", "java", "c++", "c#", "typescript", "go", "rust",
        "ruby", "php", "swift", "kotlin", "r", "matlab", "scala", "perl"
    ],
    "Web Development": [
        "html", "css", "react", "angular", "vue", "node.js", "express", "django",
        "flask", "fastapi", "spring boot", "asp.net", "next.js", "nuxt.js"
    ],
    "Mobile Development": [
        "android", "ios", "react native", "flutter", "xamarin", "swift ui",
        "kotlin multiplatform", "ionic", "cordova"
    ],
    "Data Science & ML": [
        "machine learning", "deep learning", "data analysis", "pandas", "numpy",
        "scikit-learn", "tensorflow", "pytorch", "keras", "nlp", "computer vision",
        "data visualization", "tableau", "power bi"
    ],
    "Databases": [
        "sql", "mysql", "postgresql", "mongodb", "redis", "neo4j", "cassandra",
        "dynamodb", "firebase", "elasticsearch", "oracle", "sql server"
    ],
    "Cloud & DevOps": [
        "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "jenkins",
        "github actions", "terraform", "ansible", "linux", "bash"
    ],
    "Tools & Frameworks": [
        "git", "github", "gitlab", "jira", "agile", "scrum", "rest api",
        "graphql", "microservices", "testing", "junit", "pytest", "jest"
    ],
    "Soft Skills": [
        "communication", "teamwork", "leadership", "problem solving",
        "critical thinking", "time management", "presentation", "writing"
    ]
}

# Skill synonyms and related skills
SKILL_RELATIONSHIPS = {
    "python": ["django", "flask", "fastapi", "pandas", "numpy"],
    "javascript": ["typescript", "react", "angular", "vue", "node.js"],
    "java": ["spring boot", "kotlin", "android"],
    "machine learning": ["deep learning", "data science", "python", "tensorflow", "pytorch"],
    "web development": ["html", "css", "javascript", "react", "node.js"],
    "mobile development": ["android", "ios", "react native", "flutter"],
    "cloud": ["aws", "azure", "gcp", "docker", "kubernetes"],
    "devops": ["docker", "kubernetes", "ci/cd", "linux", "bash"],
    "data analysis": ["python", "pandas", "numpy", "sql", "data visualization"],
    "backend": ["node.js", "python", "java", "rest api", "databases"],
    "frontend": ["html", "css", "javascript", "react", "vue", "angular"]
}


def populate_skills(client: Neo4jClient):
    """Populate Neo4j with skill nodes organized by category"""
    print("Populating skill taxonomy...")
    
    with client.driver.session() as session:
        for category, skills in SKILL_TAXONOMY.items():
            print(f"  Adding {category} skills...")
            for skill in skills:
                session.run(
                    """
                    MERGE (s:Skill {name: $skill_name})
                    SET s.category = $category
                    """,
                    skill_name=skill.lower().strip(),
                    category=category
                )
    
    print(f"✓ Added {sum(len(skills) for skills in SKILL_TAXONOMY.values())} skills")


def create_skill_relationships(client: Neo4jClient):
    """Create RELATED_TO relationships between related skills"""
    print("\nCreating skill relationships...")
    
    with client.driver.session() as session:
        relationship_count = 0
        for skill, related_skills in SKILL_RELATIONSHIPS.items():
            for related_skill in related_skills:
                session.run(
                    """
                    MATCH (s1:Skill {name: $skill1})
                    MATCH (s2:Skill {name: $skill2})
                    MERGE (s1)-[r:RELATED_TO]->(s2)
                    SET r.strength = 0.8
                    """,
                    skill1=skill.lower().strip(),
                    skill2=related_skill.lower().strip()
                )
                relationship_count += 1
        
    print(f"✓ Created {relationship_count} skill relationships")


def verify_population(client: Neo4jClient):
    """Verify the graph was populated correctly"""
    print("\nVerifying graph population...")
    
    with client.driver.session() as session:
        # Count skills
        result = session.run("MATCH (s:Skill) RETURN COUNT(s) as count")
        skill_count = result.single()['count']
        print(f"  Total skills: {skill_count}")
        
        # Count relationships
        result = session.run("MATCH ()-[r:RELATED_TO]->() RETURN COUNT(r) as count")
        rel_count = result.single()['count']
        print(f"  Total relationships: {rel_count}")
        
        # Show sample skills by category
        result = session.run(
            """
            MATCH (s:Skill)
            RETURN s.category as category, COUNT(s) as count
            ORDER BY count DESC
            """
        )
        print("\n  Skills by category:")
        for record in result:
            print(f"    {record['category']}: {record['count']}")


def main():
    """Main function to populate Neo4j graph"""
    print("=" * 60)
    print("Neo4j Graph Population Script")
    print("=" * 60)
    
    # Initialize client
    client = Neo4jClient()
    
    try:
        # Populate skills
        populate_skills(client)
        
        # Create relationships
        create_skill_relationships(client)
        
        # Verify
        verify_population(client)
        
        print("\n" + "=" * 60)
        print("✓ Graph population completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error during population: {e}")
        raise
    
    finally:
        client.close()


if __name__ == "__main__":
    main()
