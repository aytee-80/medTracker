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
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL
                )
            """)

            # Medications Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS medications (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    total_pills INTEGER NOT NULL,
                    dosage_per_day INTEGER NOT NULL,
                    schedule TIME WITHOUT TIME ZONE,
                    description TEXT,
                    last_taken DATE,
                    next_reminder TIMESTAMP WITHOUT TIME ZONE,
                    notify_email BOOLEAN DEFAULT TRUE
                )
            """)
            conn.commit()
            print("Tables created or already exist.")
        except Exception as e:
            print(f"Error creating tables: {e}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()