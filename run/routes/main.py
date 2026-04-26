from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime, date, timedelta
from run.db.connection import get_db_connection

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('index.html')

@main.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    user_agent = request.headers.get('User-Agent').lower()
    is_mobile = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, dosage_per_day, total_pills, schedule, last_taken FROM medications WHERE user_id = %s", (user_id,))
    meds = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    medications = []
    for row in meds:
        med = dict(zip(columns, row))
        if isinstance(med['schedule'], timedelta):
            seconds = med['schedule'].total_seconds()
            hours, remainder = divmod(seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            med['schedule_str'] = f"{int(hours):02d}:{int(minutes):02d}"
        elif med['schedule']:
            med['schedule_str'] = str(med['schedule'])[:5]
        else:
            med['schedule_str'] = 'N/A'
        medications.append(med)

    notifications = []
    current_time = datetime.now().strftime("%H:%M")

    for med in medications:
        if med['schedule_str'] != 'N/A' and med['schedule_str'] <= current_time:
            if med['last_taken'] != date.today() and med['total_pills'] > 0:
                notifications.append({
                    "type": "info",
                    "message": f"It's time to take {med['name']} ({med['dosage_per_day']} pill(s))."
                })
        if med['total_pills'] < med['dosage_per_day'] * 3 and med['total_pills'] > 0:
            notifications.append({
                "type": "warning",
                "message": f"Low pills for {med['name']}. Only {med['total_pills']} left."
            })
        if med['total_pills'] <= 0:
            notifications.append({
                "type": "danger",
                "message": f"You're out of pills for {med['name']}. Please refill."
            })

    cur.close()
    conn.close()
    return render_template('dashboard.html', medications=medications, notifications=notifications, is_mobile=is_mobile)