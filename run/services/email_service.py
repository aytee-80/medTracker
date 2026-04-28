from flask_mail import Message
import email_config

def send_welcome_email(mail, email):
    msg = Message(
        subject=" Welcome to Medication Tracker!",
        sender=email_config.EMAIL_HOST_USER,
        recipients=[email]
    )
    msg.body = """
Hi there,
Welcome to the Medication Tracker App!
We're excited to help you manage your medication schedule more effectively.
Please log in to add your first medication.
Best regards,
Medication Tracker Team
"""
    mail.send(msg)

def send_reminder_email(mail, user_email, med):
    msg = Message(
        subject=" Medication Reminder: " + med['name'],
        sender=email_config.EMAIL_HOST_USER,
        recipients=[user_email]
    )
    msg.body = f"""
Hi there,
It's time to take your medicationn "{med['name']}".
Dosage: {med['dosage_per_day']} pill(s) per day.
Please log in to confirm you've taken it.
Best regards,
Medication Tracker Team
    """
    mail.send(msg)