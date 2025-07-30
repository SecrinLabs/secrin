import os
import sys
import psycopg2

# Add root directory to sys.path for config imports
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from config import settings, get_logger

# Setup logger for this module
logger = get_logger(__name__)

base_path = os.path.join(os.path.dirname(__file__), "sql")


def ensure_migrations_table(conn):
    """Create migrations table if it doesn't exist"""
    logger.debug("Creating migrations table if not exists")
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id SERIAL PRIMARY KEY,
                filename TEXT UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    logger.debug("Migrations table ensured")

def get_applied_migrations(conn):
    """Get set of already applied migration filenames"""
    logger.debug("Fetching applied migrations from database")
    with conn.cursor() as cur:
        cur.execute("SELECT filename FROM migrations")
        applied = set(row[0] for row in cur.fetchall())
    logger.debug(f"Found {len(applied)} applied migrations")
    return applied

def apply_migration(conn, filepath):
    """Apply a single migration file"""
    filename = os.path.basename(filepath)
    try:
        logger.info(f"▶️ Applying migration: {filename}")
        with open(filepath, 'r') as f:
            sql = f.read()
        
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute("INSERT INTO migrations (filename) VALUES (%s)", (filename,))
            conn.commit()
            
        logger.info(f"✅ Successfully applied: {filename}")
        
    except Exception as e:
        logger.error(f"❌ Failed to apply {filename}: {str(e)}")
        conn.rollback()
        raise

def main():
    """Main migration runner function"""
    try:
        logger.info("🚀 Starting database migrations")
        logger.info(f"🔗 Connecting to database...")
        
        conn = psycopg2.connect(settings.DATABASE_URL)
        logger.info("✅ Database connection successful")
        
        ensure_migrations_table(conn)

        # Get all SQL migration files
        all_files = sorted(
            f for f in os.listdir(base_path) if f.endswith('.sql')
        )
        
        logger.info(f"📁 Found {len(all_files)} migration files in {base_path}")

        if not all_files:
            logger.warning("📝 No migration files found")
            return

        applied = get_applied_migrations(conn)
        pending_migrations = [f for f in all_files if f not in applied]
        
        if not pending_migrations:
            logger.info("✅ All migrations are already applied")
        else:
            logger.info(f"📋 {len(pending_migrations)} migrations to apply")

        for file in all_files:
            if file not in applied:
                apply_migration(conn, os.path.join(base_path, file))
            else:
                logger.debug(f"⏭️ Skipping {file} (already applied)")

        conn.close()
        logger.info("✅ Migration process completed successfully")
        
    except psycopg2.Error as e:
        logger.error(f"❌ Database error: {str(e)}")
        exit(1)
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
