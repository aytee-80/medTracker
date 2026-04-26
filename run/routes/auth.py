from flask import Blueprint, request, redirect, url_for, session,render_template
import bcrypt
from run.db.connection import get_db_connection
from run.services.email_service import send_welcome_email

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    from run import mail
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password'].encode('utf-8')
            hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

            conn = get_db_connection()
            if conn is None:
                return " DB connection failed"

            cur = conn.cursor()

            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            existing = cur.fetchone()

            if existing:
                return "Email already registered"

            cur.execute(
                "INSERT INTO users (email, password) VALUES (%s, %s)",
                (email, hashed)
            )
            conn.commit()

            cur.close()
            conn.close()

            send_welcome_email(mail, email)
            return redirect(url_for('main.home'))

        except Exception as e:
            print("REGISTER ERROR:", e)
            return f"Error: {e}"
    return render_template('register.html')

@auth.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password'].encode('utf-8')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, email, password FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and bcrypt.checkpw(password, user[2].encode('utf-8')):
        session['user_id'] = user[0]
        session.permanent = True
        return redirect(url_for('main.dashboard'))
    else:
        return """
            <script>
                alert("Invalid credentials");
                window.location.href='/';
            </script>
        """

@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('main.home'))