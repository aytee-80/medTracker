from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, date
import atexit
from run.db.connection import get_db_connection
from run.services.email_service import send_reminder_email

scheduler_started = False
scheduler = None

def send_reminder_emails(app, mail):
    with app.app_context():
        conn = None
        cur = None
        try:
            conn = get_db_connection()
            if conn is None:
                print("Scheduler: Database connection failed")
                return

            cur = conn.cursor()
            today = date.today()
            now_time = datetime.now().time()

            # Find pending doses for today that are due now
            cur.execute("""
                SELECT md.id, md.medication_id, md.dose_time, md.pills_count,
                       mv.name, mv.description, mv.user_id, u.email
                FROM medication_doses_v2 md
                JOIN medications_v2 mv ON md.medication_id = mv.id
                JOIN users u ON mv.user_id = u.id
                WHERE md.scheduled_date = %s
                  AND md.status = 'pending'
                  AND md.dose_time <= %s
                  AND mv.notify_email = TRUE
            """, (today, now_time))

            doses = cur.fetchall()

            for dose in doses:
                try:
                    med_data = {
                        'name': dose['name'],
                        'description': dose['description'],
                        'dose_time': dose['dose_time'].strftime('%I:%M %p'),
                        'pills_count': dose['pills_count'],
                        'scheduled_date': today
                    }
                    send_reminder_email(mail, dose['email'], med_data)
                except Exception as e:
                    print(f"Failed to send reminder for dose {dose['id']}: {e}")

            conn.commit()
        except Exception as e:
            print(f"Scheduler error: {e}")
            if conn:
                conn.rollback()
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

def start_scheduler(app, mail):
    global scheduler_started, scheduler
    if not scheduler_started:
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            lambda: send_reminder_emails(app, mail),
            'interval',
            minutes=5,
            id='medication_reminder_job',
            replace_existing=True
        )
        scheduler.start()
        scheduler_started = True
        atexit.register(lambda: scheduler.shutdown())
        print("Scheduler started")