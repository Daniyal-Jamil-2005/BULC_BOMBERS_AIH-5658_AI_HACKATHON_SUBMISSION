# Database Migrations

This directory contains SQL migration files for the Inbox Copilot MySQL database.

## Running Migrations

### Prerequisites

1. Ensure MySQL is running and accessible
2. Set the following environment variables in your `.env` file:
   ```
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=your_username
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=inbox_copilot
   ```

### Execute a Migration

From the `Back End/database` directory, run:

```bash
python run_migration.py migrations/001_add_email_credentials_table.sql
```

Or from the `Back End` directory:

```bash
python database/run_migration.py database/migrations/001_add_email_credentials_table.sql
```

### Verify Migration

After running the migration, you can verify the table was created:

```sql
SHOW TABLES LIKE 'email_credentials';
DESCRIBE email_credentials;
```

## Migration Files

### 001_add_email_credentials_table.sql

**Purpose**: Add the `email_credentials` table for storing encrypted Gmail/Outlook credentials

**Changes**:
- Creates `email_credentials` table with fields:
  - `id`: Primary key (UUID)
  - `user_id`: Foreign key to users table
  - `provider`: Email provider ('gmail' or 'outlook')
  - `email_address`: User's email address
  - `credentials`: Encrypted JSON containing OAuth tokens or app passwords
  - `created_at`: Timestamp of creation
  - `updated_at`: Timestamp of last update
- Adds unique constraint on (user_id, provider)
- Adds index on (user_id, provider) for performance

**Notes**:
- This table replaces the deprecated `oauth_tokens` table
- The `oauth_tokens` table is not dropped for backward compatibility
- See migration file for instructions on migrating existing data

## Creating New Migrations

1. Create a new SQL file in this directory with naming convention: `XXX_description.sql`
2. Add descriptive comments at the top of the file
3. Write idempotent SQL (use `IF NOT EXISTS`, `IF EXISTS`, etc.)
4. Test the migration on a development database first
5. Document the migration in this README

## Rollback

Currently, rollback is manual. To rollback a migration:

1. Identify the changes made by the migration
2. Write SQL statements to reverse those changes
3. Execute them manually or create a rollback script

Example rollback for 001_add_email_credentials_table.sql:

```sql
DROP TABLE IF EXISTS email_credentials;
DROP INDEX IF EXISTS idx_email_credentials_user ON email_credentials;
```
