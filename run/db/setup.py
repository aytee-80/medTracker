from run.db.connection import get_db_connection

def create_tables(app):
    with app.app_context():
        conn = get_db_connection()
        if conn is None:
            return
        cur = conn.cursor()
        try:
            # Users Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users_v2 (
                     id UUID PRIMARY KEY,
                     email TEXT UNIQUE NOT NULL,
                     username TEXT,
                     profile_picture TEXT,
                     created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Medications Table
            cur.execute("""
                 CREATE TABLE IF NOT EXISTS medications_v2 (
                    id SERIAL PRIMARY KEY,
                    user_id UUID NOT NULL,
                    name TEXT NOT NULL,
                    total_pills INTEGER NOT NULL,
                    dosage_per_day INTEGER NOT NULL,
                    schedule TIME,
                    description TEXT,
                    last_taken DATE,
                    next_reminder TIMESTAMP,
                    notify_email BOOLEAN DEFAULT TRUE
                )
            """)
            conn.commit()
            print("Tables created or already exist.")
        except Exception as e:
            print(f" Error creating tables: {e}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()