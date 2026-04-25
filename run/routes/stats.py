from flask import Blueprint, render_template, redirect, url_for, session, make_response
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
        return redirect(url_for('main.home'))

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, dosage_per_day, total_pills, last_taken FROM medications WHERE user_id = %s", (user_id,))
    meds = cur.fetchall()
    stats_data = {
        "total_medications": len(meds),
        "total_doses_scheduled": 0,
        "total_doses_taken": 0,
        "missed_doses": 0,
        "adherence_rate": 0
    }

    for med in meds:
        name, dosage, total_pills, last_taken = med
        if last_taken:
            days_prescribed = (datetime.now().date() - last_taken).days
            scheduled_doses = max(0, days_prescribed * dosage)
            taken_doses = total_pills // dosage if total_pills else 0
        else:
            scheduled_doses = 0
            taken_doses = 0
        stats_data["total_doses_scheduled"] += scheduled_doses
        stats_data["total_doses_taken"] += taken_doses

    stats_data["missed_doses"] = max(0, stats_data["total_doses_scheduled"] - stats_data["total_doses_taken"])
    if stats_data["total_doses_scheduled"] > 0:
        stats_data["adherence_rate"] = round((stats_data["total_doses_taken"] / stats_data["total_doses_scheduled"]) * 100, 2)

    cur.close()
    conn.close()
    return render_template('statistics.html', stats=stats_data)

@stats.route('/export_statistics/csv')
def export_csv():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, dosage_per_day, total_pills, last_taken FROM medications WHERE user_id = %s", (user_id,))
    meds = cur.fetchall()
    df = pd.DataFrame(meds, columns=['Name', 'Dosage per Day', 'Total Pills', 'Last Taken'])

    si = StringIO()
    df.to_csv(si, index=False)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=medication_stats.csv"
    output.headers["Content-type"] = "text/csv"
    cur.close()
    conn.close()
    return output

@stats.route('/export_statistics/pdf')
def export_pdf():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, dosage_per_day, total_pills, last_taken FROM medications WHERE user_id = %s", (user_id,))
    meds = cur.fetchall()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    story = [Paragraph("📄 Medication Report", styles['Title']), Spacer(1, 24)]

    for med in meds:
        name, dosage, total, last_taken = med
        last_taken_str = last_taken.strftime("%Y-%m-%d") if last_taken else "N/A"
        med_info = f"<b>Name:</b> {name}<br/><b>Dosage/Day:</b> {dosage}<br/><b>Total Pills:</b> {total}<br/><b>Last Taken:</b> {last_taken_str}"
        story.append(Paragraph(med_info, styles['Normal']))
        story.append(Spacer(1, 12))

    doc.build(story)
    pdf_output = buffer.getvalue()
    buffer.close()
    response = make_response(pdf_output)
    response.headers['Content-Disposition'] = 'attachment; filename=medication_report.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    cur.close()
    conn.close()
    return response