from flask import Blueprint, request, redirect, url_for, session,render_template
import bcrypt
from run.db.connection import get_db_connection
from run.services.email_service import send_welcome_email
import requests
import config

auth = Blueprint('auth', __name__)



@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        res = requests.post(
            f"{config.SUPABASE_URL}/auth/v1/signup",
            json={
                "email": email,
                "password": password
            },
            headers={
                "apikey": config.SUPABASE_KEY,
                "Content-Type": "application/json"
            }
        )

        data = res.json()

        if res.status_code == 200:
            return "Check your email to confirm your account"
        else:
            return f"Error: {data}"

    return render_template('register.html')

@auth.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    res = requests.post(
        f"{config.SUPABASE_URL}/auth/v1/token?grant_type=password",
        json={
            "email": email,
            "password": password
        },
        headers={
            "apikey": config.SUPABASE_KEY,
            "Content-Type": "application/json"
        }
    )

    data = res.json()

    if res.status_code == 200:
        session.clear()

        session['user_id'] = data['user']['id']
        session['access_token'] = data['access_token']

        print("USER LOGGED IN:", session.get('user_id'))

        return redirect(url_for('main.dashboard'))
         
    else:
        return "Invalid credentials"

@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('main.home'))