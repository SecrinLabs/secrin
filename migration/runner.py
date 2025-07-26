import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:10514912@localhost:5432/devsecrin")
base_path = os.path.join(os.path.dirname(__file__), "sql")

def ensure_migrations_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id SERIAL PRIMARY KEY,
                filename TEXT UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def get_applied_migrations(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT filename FROM migrations")
        return set(row[0] for row in cur.fetchall())

def apply_migration(conn, filepath):
    with open(filepath, 'r') as f:
        sql = f.read()
    filename = os.path.basename(filepath)
    with conn.cursor() as cur:
        print(f"▶️  Applying {filename}...")
        cur.execute(sql)
        cur.execute("INSERT INTO migrations (filename) VALUES (%s)", (filename,))
        conn.commit()
        print(f"✅ Applied {filename}")

def main():
    conn = psycopg2.connect(DATABASE_URL)
    ensure_migrations_table(conn)

    all_files = sorted(
        f for f in os.listdir(base_path) if f.endswith('.sql')
    )

    applied = get_applied_migrations(conn)

    for file in all_files:
        if file not in applied:
            apply_migration(conn, os.path.join(base_path, file))
        else:
            print(f"⏭️  Skipping {file} (already applied)")

    conn.close()

if __name__ == "__main__":
    main()
