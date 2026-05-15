"""
Migration Runner for MySQL Database
Executes SQL migration files in the migrations directory
"""

import mysql.connector
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the Back End directory (one level up from database/)
load_dotenv(Path(__file__).parent.parent / '.env')

def run_migration(migration_file: str):
    """Run a single migration file"""
    # Database configuration
    config = {
        'host': os.getenv("MYSQL_HOST", "localhost"),
        'port': int(os.getenv("MYSQL_PORT", "3306")),
        'user': os.getenv("MYSQL_USER"),
        'password': os.getenv("MYSQL_PASSWORD"),
        'database': os.getenv("MYSQL_DATABASE")
    }
    
    # Check if required environment variables are set
    if not config['user'] or not config['password'] or not config['database']:
        print("Error: Missing required environment variables (MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE)")
        print("Please set these variables in your .env file or environment")
        sys.exit(1)
    
    # Read migration file
    migration_path = Path(__file__).parent / 'migrations' / migration_file
    if not migration_path.exists():
        print(f"Error: Migration file not found: {migration_path}")
        sys.exit(1)
    
    with open(migration_path, 'r') as f:
        sql_content = f.read()
    
    # Split SQL statements (simple split by semicolon)
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
    
    # Connect to database
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        print(f"Running migration: {migration_file}")
        print(f"Database: {config['database']} at {config['host']}:{config['port']}")
        print("-" * 60)
        
        # Execute each statement
        for i, statement in enumerate(statements, 1):
            # Skip comments
            if statement.startswith('--'):
                continue
            
            try:
                cursor.execute(statement)
                connection.commit()
                print(f"✓ Statement {i} executed successfully")
            except mysql.connector.Error as err:
                print(f"✗ Error executing statement {i}: {err}")
                print(f"Statement: {statement[:100]}...")
                connection.rollback()
                raise
        
        print("-" * 60)
        print(f"✓ Migration completed successfully!")
        
        cursor.close()
        connection.close()
        
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <migration_file>")
        print("Example: python run_migration.py 001_add_email_credentials_table.sql")
        sys.exit(1)
    
    migration_file = sys.argv[1]
    run_migration(migration_file)
