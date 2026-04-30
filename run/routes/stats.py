from flask import Blueprint, render_template, redirect, url_for, session, make_response, flash
from datetime import datetime, date
import pandas as pd
from io import StringIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io
from run.db.connection import get_db_connection

stats = Blueprint('stats', __name__)

@stats.route('/statistics')
def statistics():
    if 'user_id' not in session:
        flash("Please log in to view statistics", "danger")
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
        
        # Total medications
        cur.execute("SELECT COUNT(*) FROM medications_v2 WHERE user_id = %s", (user_id,))
        total_medications = cur.fetchone()[0]
        
        # Doses taken (from medication_doses_v2 status)
        cur.execute("""
            SELECT COUNT(*) 
            FROM medication_doses_v2 md
            JOIN medications_v2 m ON md.medication_id = m.id
            WHERE m.user_id = %s AND md.status = 'taken'
        """, (user_id,))
        total_doses_taken = cur.fetchone()[0]
        
        # Missed doses
        cur.execute("""
            SELECT COUNT(*) 
            FROM medication_doses_v2 md
            JOIN medications_v2 m ON md.medication_id = m.id
            WHERE m.user_id = %s AND md.status = 'missed'
        """, (user_id,))
        missed_doses = cur.fetchone()[0]
        
        # Calculate adherence rate
        total_recorded = total_doses_taken + missed_doses
        adherence_rate = round((total_doses_taken / total_recorded * 100), 1) if total_recorded > 0 else 0
        
        stats_data = {
            "total_medications": total_medications,
            "total_doses_taken": total_doses_taken,
            "missed_doses": missed_doses,
            "adherence_rate": adherence_rate
        }
        
        return render_template('statistics.html', stats=stats_data)
        
    except Exception as e:
        print(f"Statistics error: {e}")
        flash("Could not load statistics", "danger")
        return redirect(url_for('main.dashboard'))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@stats.route('/export_statistics/csv')
def export_csv():
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
        # Only select columns that exist in your schema
        cur.execute("""
            SELECT name, dosage_per_day, total_pills, description, created_at 
            FROM medications_v2 
            WHERE user_id = %s
        """, (user_id,))
        meds = cur.fetchall()
        
        df = pd.DataFrame(meds, columns=['Name', 'Dosage per Day', 'Total Pills', 'Description', 'Created At'])
        si = StringIO()
        df.to_csv(si, index=False)
        
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=medication_stats.csv"
        output.headers["Content-type"] = "text/csv"
        return output
        
    except Exception as e:
        print(f"CSV export error: {e}")
        flash("Failed to export CSV", "danger")
        return redirect(url_for('stats.statistics'))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@stats.route('/export_statistics/pdf')
def export_pdf():
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
            SELECT name, dosage_per_day, total_pills, description, created_at 
            FROM medications_v2 
            WHERE user_id = %s
        """, (user_id,))
        meds = cur.fetchall()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer)
        styles = getSampleStyleSheet()
        story = [Paragraph("Medication Report", styles['Title']), Spacer(1, 24)]

        for med in meds:
            name, dosage, total, description, created_at = med
            created_str = created_at.strftime("%Y-%m-%d") if created_at else "N/A"
            desc_str = description if description else "No notes"
            med_info = f"<b>Name:</b> {name}<br/><b>Dosage/Day:</b> {dosage}<br/><b>Total Pills:</b> {total}<br/><b>Added:</b> {created_str}<br/><b>Notes:</b> {desc_str}"
            story.append(Paragraph(med_info, styles['Normal']))
            story.append(Spacer(1, 12))

        doc.build(story)
        pdf_output = buffer.getvalue()
        buffer.close()
        
        response = make_response(pdf_output)
        response.headers['Content-Disposition'] = 'attachment; filename=medication_report.pdf'
        response.headers['Content-Type'] = 'application/pdf'
        return response
        
    except Exception as e:
        print(f"PDF export error: {e}")
        flash("Failed to export PDF", "danger")
        return redirect(url_for('stats.statistics'))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()