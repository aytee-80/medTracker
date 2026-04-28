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
                description TEXT,
                notify_email BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            )
            """)
            cur.execute("""CREATE TABLE IF NOT EXISTS medication_doses_v2 (
                    id SERIAL PRIMARY KEY,
                    medication_id INTEGER NOT NULL REFERENCES medications_v2(id) ON DELETE CASCADE,

                    dose_time TIME NOT NULL,
                    pills_count INTEGER NOT NULL,

                    status TEXT DEFAULT 'pending',
                    -- pending | taken | missed

                    scheduled_date DATE NOT NULL DEFAULT CURRENT_DATE,

                    taken_at TIMESTAMP NULL,

                    created_at TIMESTAMP DEFAULT NOW()
                )""")
            conn.commit()
            print("Tables created or already exist.")
        except Exception as e:
            print(f" Error creating tables: {e}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()