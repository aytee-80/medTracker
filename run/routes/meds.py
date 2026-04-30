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

from flask import jsonify

@meds.route('/take_medication', methods=['POST'])
def take_medication():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    dose_id = request.form.get('dose_id')
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT medication_id, pills_count, status
            FROM medication_doses_v2
            WHERE id = %s
        """, (dose_id,))
        dose = cur.fetchone()

        if not dose:
            return jsonify({'success': False, 'error': 'Dose not found'}), 404

        med_id, pills, status = dose

        if status != 'pending':
            return jsonify({'success': False, 'error': 'Already taken'}), 400

        # update dose
        cur.execute("""
            UPDATE medication_doses_v2
            SET status = 'taken', taken_at = NOW()
            WHERE id = %s
        """, (dose_id,))

        # update pills
        cur.execute("""
            UPDATE medications_v2
            SET total_pills = GREATEST(0, total_pills - %s)
            WHERE id = %s
        """, (pills, med_id))

        conn.commit()

        # response data
        cur.execute("""
            SELECT total_pills
            FROM medications_v2
            WHERE id = %s
        """, (med_id,))
        remaining = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM medication_doses_v2 d
            JOIN medications_v2 m ON d.medication_id = m.id
            WHERE m.user_id = %s
              AND d.status = 'taken'
              AND DATE(d.taken_at) = CURRENT_DATE
        """, (session['user_id'],))
        taken_today = cur.fetchone()[0]

        return jsonify({
            'success': True,
            'remaining_pills': remaining,
            'taken_today': taken_today
        })

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

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
    conn = None
    cur = None
    
    try:
        conn = get_db_connection()
        if conn is None:
            flash("Database connection failed", "danger")
            return redirect(url_for('main.dashboard'))
            
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, dosage_per_day, total_pills, description, created_at
            FROM medications_v2
            WHERE user_id = %s
            ORDER BY name
        """, (user_id,))
        
        # Convert tuples to dictionaries safely
        columns = [desc[0] for desc in cur.description]
        medications = [dict(zip(columns, row)) for row in cur.fetchall()]
        
        # Format dates in Python to avoid Jinja2 errors
        for med in medications:
            if med['created_at'] and hasattr(med['created_at'], 'strftime'):
                med['created_at_str'] = med['created_at'].strftime('%b %d, %Y')
            else:
                med['created_at_str'] = str(med['created_at'])[:10] if med['created_at'] else 'N/A'
                
        return render_template('print_guide.html', medications=medications)
        
    except Exception as e:
        # Show exact error for debugging
        print(f"Print guide error: {e}")
        flash(f"Error loading medications: {str(e)}", "danger")
        return redirect(url_for('main.dashboard'))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()