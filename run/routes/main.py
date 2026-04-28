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
    cur.execute("""
         SELECT 
        m.id as med_id,
        m.name,
        m.total_pills,
        m.dosage_per_day,
        d.id as dose_id,
        d.dose_time,
        d.pills_count,
        d.status
    FROM medications_v2 m
    LEFT JOIN medication_doses_v2 d 
        ON m.id = d.medication_id
    WHERE m.user_id = %s
    ORDER BY m.id, d.dose_time
    """, (user_id,))
    rows = cur.fetchall()

    medications = {}
    for row in rows:
        med_id = row[0]

        if med_id not in medications:
            medications[med_id] = {
                "id": med_id,
                "name": row[1],
                "total_pills": row[2],
                "dosage_per_day": row[3],
                "doses": []
            }

        if row[4]:  # if dose exists
            medications[med_id]["doses"].append({
                "id": row[4],
                "time": str(row[5])[:5],
                "pills": row[6],
                "status": row[7]
            })

    medications = list(medications.values())

    notifications = []
    current_time = datetime.now().strftime("%H:%M")

    for med in medications:
        for dose in med["doses"]:
            if dose["time"] <= current_time and dose["status"] == "pending":
                notifications.append({
                    "type": "info",
                    "message": f"It's time to take {med['name']} ({dose['pills']} pill(s)) at {dose['time']}."
                })

        # Low pills warning (keep this)
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

@main.route('/api/taken_count')
def api_taken_count():
    if 'user_id' not in session:
        return {'count': 0}, 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) 
        FROM medication_doses_v2 d 
        JOIN medications_v2 m ON d.medication_id = m.id 
        WHERE m.user_id = %s 
        AND d.status = 'taken' 
        AND DATE(d.taken_at) = CURRENT_DATE
    """, (session['user_id'],))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    return {'count': count}