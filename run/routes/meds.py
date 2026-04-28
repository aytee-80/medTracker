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
    total_pills = int(request.form['total_pills'])
    dosage_per_day = int(request.form['dosage_per_day'])
    description = request.form.get('description')

    dose_times = request.form.getlist('dose_times[]')
    pills_per_dose = request.form.getlist('pills_per_dose[]')

    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Insert medication
    cur.execute("""
        INSERT INTO medications_v2 (user_id, name, total_pills, dosage_per_day, description)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (user_id, name, total_pills, dosage_per_day, description))

    med_id = cur.fetchone()[0]

    # 2. Insert doses
    today = date.today()

    for i in range(len(dose_times)):
        cur.execute("""
            INSERT INTO medication_doses_v2 (medication_id, dose_time, pills_count, scheduled_date)
            VALUES (%s, %s, %s, %s)
        """, (med_id, dose_times[i], pills_per_dose[i], today))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('main.dashboard'))

@meds.route('/take_medication', methods=['POST'])
def take_medication():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    dose_id = request.form.get('dose_id')
    
    # Handle AJAX requests
    is_ajax = request.accept_mimetypes['application/json']
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get dose info
        cur.execute("""
            SELECT medication_id, pills_count, status
            FROM medication_doses_v2 
            WHERE id = %s
        """, (dose_id,))
        dose = cur.fetchone()

        if not dose:
            if is_ajax:
                return {'success': False, 'error': 'Dose not found'}, 404
            flash("Dose not found", "error")
            return redirect(url_for('main.dashboard'))

        med_id, pills, status = dose
        
        if status != 'pending':
            if is_ajax:
                return {'success': False, 'error': 'Dose already taken'}, 400
            flash("This dose was already taken", "info")
            return redirect(url_for('main.dashboard'))

        # Mark as taken
        cur.execute("""
            UPDATE medication_doses_v2
            SET status = 'taken', taken_at = NOW()
            WHERE id = %s
        """, (dose_id,))

        # Subtract pills
        cur.execute("""
            UPDATE medications_v2
            SET total_pills = GREATEST(0, total_pills - %s)
            WHERE id = %s
        """, (pills, med_id))
        conn.commit()
        
        if is_ajax:
            # Return updated counts for frontend
            cur.execute("SELECT COUNT(*) FROM medication_doses_v2 d JOIN medications_v2 m ON d.medication_id = m.id WHERE m.user_id = %s AND d.status = 'taken' AND DATE(d.taken_at) = CURRENT_DATE", (session['user_id'],))
            taken_today = cur.fetchone()[0]
            
            cur.execute("SELECT total_pills FROM medications_v2 WHERE id = %s", (med_id,))
            remaining = cur.fetchone()[0]
            
            return {
                'success': True,
                'taken_today': taken_today,
                'remaining_pills': remaining
            }
        
        flash("✓ Dose marked as taken!", "success")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "success": True,
                "message": "Dose taken"
            })
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        conn.rollback()
        if is_ajax:
            return {'success': False, 'error': str(e)}, 500
        flash(f"Error: {e}", "error")
        return redirect(url_for('main.dashboard'))
    finally:
        cur.close()
        conn.close()  
    

@meds.route('/delete_medication', methods=['POST'])
def delete_medication():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    med_id = request.form['med_id']
    user_id = session['user_id']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM medications_v2 WHERE id = %s AND user_id = %s", (med_id, user_id))
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
    cur.execute("SELECT id, name, dosage_per_day, total_pills, schedule, last_taken, description FROM medications_v2 WHERE user_id = %s", (user_id,))
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