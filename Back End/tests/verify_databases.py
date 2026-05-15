"""
Database Verification Script
Checks MySQL and Neo4j connections and reports what data exists.
Run from Back End directory: python database/verify_databases.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')

# ── MySQL ──────────────────────────────────────────────────────────────────
def verify_mysql():
    print("\n" + "="*50)
    print("MYSQL VERIFICATION")
    print("="*50)
    try:
        import mysql.connector
        config = {
            'host':     os.getenv("MYSQL_HOST", "localhost"),
            'port':     int(os.getenv("MYSQL_PORT", "3306")),
            'user':     os.getenv("MYSQL_USER"),
            'password': os.getenv("MYSQL_PASSWORD"),
            'database': os.getenv("MYSQL_DATABASE"),
        }
        print(f"Connecting to {config['host']}:{config['port']} / {config['database']} as {config['user']}")
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        # List all tables
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\nTables found ({len(tables)}): {tables}")

        # Row counts for each table
        print("\nRow counts:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            count = cursor.fetchone()[0]
            status = "✓" if count > 0 else "○"
            print(f"  {status} {table}: {count} rows")

        cursor.close()
        conn.close()
        print("\n✓ MySQL connection OK")
        return True

    except Exception as e:
        print(f"\n✗ MySQL error: {e}")
        return False


# ── Neo4j ──────────────────────────────────────────────────────────────────
def verify_neo4j():
    print("\n" + "="*50)
    print("NEO4J VERIFICATION")
    print("="*50)
    try:
        from neo4j import GraphDatabase
        uri      = os.getenv("NEO4J_URI")
        user     = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")

        print(f"Connecting to {uri} as {user}")
        driver = GraphDatabase.driver(uri, auth=(user, password))

        with driver.session() as session:
            # Node counts by label
            result = session.run("CALL db.labels() YIELD label RETURN label")
            labels = [r["label"] for r in result]
            print(f"\nNode labels found ({len(labels)}): {labels}")

            print("\nNode counts:")
            for label in labels:
                result = session.run(f"MATCH (n:{label}) RETURN COUNT(n) as count")
                count = result.single()["count"]
                status = "✓" if count > 0 else "○"
                print(f"  {status} {label}: {count} nodes")

            # Relationship counts
            result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")
            rel_types = [r["relationshipType"] for r in result]
            print(f"\nRelationship types: {rel_types}")

            print("\nRelationship counts:")
            for rel in rel_types:
                result = session.run(f"MATCH ()-[r:{rel}]->() RETURN COUNT(r) as count")
                count = result.single()["count"]
                status = "✓" if count > 0 else "○"
                print(f"  {status} {rel}: {count}")

        driver.close()
        print("\n✓ Neo4j connection OK")
        return True

    except Exception as e:
        print(f"\n✗ Neo4j error: {e}")
        return False


if __name__ == "__main__":
    mysql_ok  = verify_mysql()
    neo4j_ok  = verify_neo4j()

    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"  MySQL:  {'✓ Connected' if mysql_ok  else '✗ Failed'}")
    print(f"  Neo4j:  {'✓ Connected' if neo4j_ok  else '✗ Failed'}")
