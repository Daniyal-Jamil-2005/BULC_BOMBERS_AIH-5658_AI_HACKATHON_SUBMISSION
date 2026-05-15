"""
Database migration script for Inbox Copilot
Runs the schema.sql file to create all tables
"""

import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migrations():
    """Run database migrations"""
    print("🔄 Starting database migrations...")
    
    # Database configuration
    config = {
        'host': os.getenv("MYSQL_HOST", "localhost"),
        'port': int(os.getenv("MYSQL_PORT", "3306")),
        'user': os.getenv("MYSQL_USER"),
        'password': os.getenv("MYSQL_PASSWORD"),
        'database': os.getenv("MYSQL_DATABASE")
    }
    
    try:
        # Connect to MySQL
        print(f"📡 Connecting to MySQL at {config['host']}:{config['port']}...")
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Read schema file
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        print(f"📄 Reading schema from {schema_path}...")
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Split by semicolons and execute each statement
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        print(f"⚙️  Executing {len(statements)} SQL statements...")
        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    cursor.execute(statement)
                    print(f"  ✓ Statement {i}/{len(statements)} executed")
                except mysql.connector.Error as err:
                    print(f"  ⚠️  Warning on statement {i}: {err}")
        
        connection.commit()
        print("✅ Database migrations completed successfully!")
        
        # Show created tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"\n📊 Created tables ({len(tables)}):")
        for table in tables:
            print(f"  • {table[0]}")
        
        cursor.close()
        connection.close()
        
    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    run_migrations()
