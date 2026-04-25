from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, date, timedelta
import atexit
from run.db.connection import get_db_connection
from run.services.email_service import send_reminder_email

scheduler_started = False
scheduler = None

def send_reminder_emails(app, mail):
    with app.app_context():
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            today = date.today()
            cur.execute("SELECT * FROM medications WHERE notify_email = TRUE AND next_reminder <= NOW()")
            meds = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            meds_with_cols = [dict(zip(columns, row)) for row in meds]

            now = datetime.now()
            for med in meds_with_cols:
                if med['last_taken'] != today and med['total_pills'] > 0:
                    user_id = med['user_id']
                    cur.execute("SELECT email FROM users WHERE id = %s", (user_id,))
                    user = cur.fetchone()
                    if user:
                        send_reminder_email(mail, user[0], med)

                # Reschedule reminder
                schedule_str = str(med['schedule'])[:5]
                hour, minute = map(int, schedule_str.split(':'))
                next_reminder = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_reminder <= now:
                    next_reminder += timedelta(days=1)
                cur.execute("UPDATE medications SET next_reminder = %s WHERE id = %s", (next_reminder, med['id']))
                conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Scheduler error: {e}")

def start_scheduler(app, mail):
    global scheduler_started, scheduler
    if not scheduler_started:
        scheduler = BackgroundScheduler()
        scheduler.add_job(lambda: send_reminder_emails(app, mail), 'interval', minutes=1)
        scheduler.start()
        scheduler_started = True
        atexit.register(lambda: scheduler.shutdown())