from flask import Blueprint, request, redirect, url_for, session, render_template, flash
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
            flash("Check your email to confirm your account", "success")
            return redirect(url_for('main.home'))
        else:
            error_msg = data.get('msg', data.get('error_description', 'Registration failed'))
            flash(f"Error: {error_msg}", "danger")
            return redirect(url_for('auth.register'))

    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
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
            flash("Welcome back! ", "success")
            return redirect(url_for('main.dashboard'))
        else:
            error_msg = data.get('msg', data.get('error_description', 'Invalid credentials'))
            flash(f"Error: {error_msg}", "danger")
            return redirect(url_for('main.home'))
    
    return render_template('login.html')

@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('access_token', None)
    flash("You've been logged out. See you soon!", "info")
    return redirect(url_for('main.home'))


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        res = requests.post(
            f"{config.SUPABASE_URL}/auth/v1/recover",
            json={
                "email": email,
                "redirectTo": "https://medtracker.up.railway.app/reset-password"
            },
            headers={
                "apikey": config.SUPABASE_KEY,
                "Content-Type": "application/json"
            }
        )

        if res.status_code in [200, 204]:
            flash("Password reset link sent to your email", "success")
        else:
            flash("Error sending reset email", "danger")

        return redirect(url_for('main.home'))

    return render_template('forgot_password.html')

@auth.route('/update-password', methods=['POST'])
def update_password():
    data = request.json
    new_password = data.get("password")
    access_token = data.get("access_token")

    if not access_token:
        return {"error": "Missing token"}, 400

    # STEP 1: create authenticated request context
    headers = {
        "apikey": config.SUPABASE_KEY,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    requests.post(
    f"{config.SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
    json={
        "refresh_token": request.json.get("refresh_token")
    },
    headers={
        "apikey": config.SUPABASE_KEY
    }
)
    # STEP 2: update password (IMPORTANT: must include user scope token)
    res = requests.put(
        f"{config.SUPABASE_URL}/auth/v1/user",
        json={"password": new_password},
        headers=headers
    )

    if res.status_code in [200, 204]:
        return {"message": "Password updated successfully"}

    return {
        "error": "Failed to update password",
        "details": res.json()
    }, 400

@auth.route('/reset-password', methods=['GET'])
def reset_password():
    return render_template('reset_password.html')