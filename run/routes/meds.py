from flask import Blueprint, request, redirect, url_for, session, render_template, flash
from datetime import datetime, timedelta, date
from run.db.connection import get_db_connection

meds = Blueprint('meds', __name__)

@meds.route('/add_medication')
def add_medication():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))
    return render_template('add_medication.html')

@meds.route('/save_medication', methods=['POST'])
def save_medication():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    user_id = session['user_id']
    name = request.form['name']
    total_pills = request.form['total_pills']
    dosage_per_day = request.form['dosage_per_day']
    schedule = request.form['schedule']

    now = datetime.now()
    hour, minute = map(int, schedule.split(':'))
    next_reminder = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if next_reminder < now:
        next_reminder += timedelta(days=1)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO medications (user_id, name, total_pills, dosage_per_day, schedule, next_reminder)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (user_id, name, total_pills, dosage_per_day, schedule, next_reminder))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('main.dashboard'))

@meds.route('/take_medication', methods=['POST'])
def take_medication():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    med_id = request.form['med_id']
    user_id = session['user_id']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT total_pills, dosage_per_day FROM medications WHERE id = %s AND user_id = %s", (med_id, user_id))
    med = cur.fetchone()

    if med:
        total_pills, dosage = med[0], med[1]
        new_count = total_pills - dosage
        today = date.today()

        if new_count <= 0:
            cur.execute("DELETE FROM medications WHERE id = %s AND user_id = %s", (med_id, user_id))
            flash("You're out of pills. Please refill.")
        else:
            cur.execute("""
                UPDATE medications
                SET total_pills = %s, last_taken = %s
                WHERE id = %s AND user_id = %s
            """, (new_count, today, med_id, user_id))

        conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('main.dashboard'))

@meds.route('/delete_medication', methods=['POST'])
def delete_medication():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    med_id = request.form['med_id']
    user_id = session['user_id']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM medications WHERE id = %s AND user_id = %s", (med_id, user_id))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('main.dashboard'))

@meds.route('/print_guide')
def print_guide():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, dosage_per_day, total_pills, schedule, last_taken, description FROM medications WHERE user_id = %s", (user_id,))
    meds_data = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    medications = []

    for row in meds_data:
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

    cur.close()
    conn.close()
    return render_template('print_guide.html', medications=medications)