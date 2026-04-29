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

@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        new_password = request.form['password']

        access_token = request.args.get('access_token')

        if not access_token:
            flash("Invalid or expired reset link", "danger")
            return redirect(url_for('main.home'))

        res = requests.put(
            f"{config.SUPABASE_URL}/auth/v1/user",
            json={
                "password": new_password
            },
            headers={
                "apikey": config.SUPABASE_KEY,
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )

        if res.status_code == 200:
            flash("Password updated successfully. Please log in.", "success")
            return redirect(url_for('main.home'))
        else:
            flash("Failed to update password", "danger")

    return render_template('reset_password.html')