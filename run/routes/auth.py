from flask import Blueprint, request, redirect, url_for, session, render_template, flash, jsonify
import requests
import config

auth = Blueprint('auth', __name__)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form.get('confirm_password', '')

        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for('auth.register'))
        
        if len(password) < 8:
            flash("Password must be at least 8 characters", "danger")
            return redirect(url_for('auth.register'))

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
            error_msg = data.get('msg') or data.get('error_description') or data.get('error', 'Registration failed')
            
            if 'password' in error_msg.lower() and 'similar' in error_msg.lower():
                error_msg = "New password cannot be similar to your previous password. Please choose a different password."
            elif 'weak password' in error_msg.lower():
                error_msg = "Password is too weak. Please use at least 8 characters with a mix of letters, numbers, and symbols."
            elif 'user already registered' in error_msg.lower() or 'duplicate' in error_msg.lower():
                error_msg = "An account with this email already exists. Please sign in instead."
            
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
            flash("Welcome back!", "success")
            return redirect(url_for('main.dashboard'))
        else:
            error_msg = data.get('msg') or data.get('error_description') or 'Invalid credentials'
            
            if 'invalid login credentials' in error_msg.lower():
                error_msg = "Invalid email or password. Please try again."
            elif 'email not confirmed' in error_msg.lower():
                error_msg = "Please confirm your email address before signing in. Check your inbox for the confirmation link."
            
            flash(f"Error: {error_msg}", "danger")
            return redirect(url_for('main.home'))
    
    return render_template('login.html')


@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('access_token', None)
    flash("You have been logged out. See you soon!", "info")
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
            flash("If an account exists with that email, a password reset link has been sent.", "success")
        else:
            try:
                error_data = res.json()
                error_msg = error_data.get('error_description') or error_data.get('msg') or 'Failed to send reset email'
                flash(f"Error: {error_msg}", "danger")
            except:
                flash("Error sending reset email. Please try again.", "danger")

        return redirect(url_for('main.home'))

    return render_template('forgot_password.html')


@auth.route('/update-password', methods=['POST'])
def update_password():
    """
    Handle password update via Supabase Auth API.
    Uses regular form POST with flash messages (not AJAX).
    Expects form data: password, access_token, refresh_token
    """
    try:
        # Get form data (not JSON)
        new_password = request.form.get("password")
        access_token = request.form.get("access_token")
        refresh_token = request.form.get("refresh_token")  # Not used by Supabase but kept for completeness

        if not access_token:
            flash("Session expired. Please request a new reset link.", "danger")
            return redirect(url_for('auth.forgot_password'))
        
        if not new_password or len(new_password) < 8:
            flash("Password must be at least 8 characters", "danger")
            return redirect(url_for('auth.reset_password'))

        headers = {
            "apikey": config.SUPABASE_KEY,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        res = requests.put(
            f"{config.SUPABASE_URL}/auth/v1/user",
            json={"password": new_password},
            headers=headers,
            timeout=30
        )

        if res.status_code in [200, 204]:
            flash("Password updated successfully. Please log in with your new password.", "success")
            return redirect(url_for('main.home'))

        # Parse Supabase error
        try:
            error_details = res.json()
        except:
            error_details = {"raw_response": res.text}

        raw_error = error_details.get('msg') or error_details.get('error_description') or error_details.get('error') or str(error_details)
        
        # Map Supabase errors to user-friendly flash messages
        if 'password' in raw_error.lower():
            if 'similar' in raw_error.lower():
                flash("New password cannot be similar to your previous password. Please choose a more different password.", "danger")
            elif 'weak' in raw_error.lower() or 'strength' in raw_error.lower():
                flash("Password does not meet security requirements. Use at least 8 characters with letters, numbers, and symbols.", "danger")
            elif 'previously used' in raw_error.lower():
                flash("You cannot reuse a previous password. Please choose a new password.", "danger")
            elif 'pwned' in raw_error.lower() or 'common' in raw_error.lower():
                flash("This password is too common or compromised. Please choose a stronger password.", "danger")
            elif 'not enough different' in raw_error.lower():
                flash("New password must be sufficiently different from your previous password.", "danger")
            else:
                flash(f"Password error: {raw_error}", "danger")
        elif 'token' in raw_error.lower() or 'expired' in raw_error.lower():
            flash("Reset link has expired. Please request a new password reset.", "danger")
        else:
            flash(f"Failed to update password: {raw_error}", "danger")

        return redirect(url_for('auth.reset_password'))

    except requests.exceptions.Timeout:
        flash("The request took too long. Please check your connection and try again.", "danger")
        return redirect(url_for('auth.reset_password'))
    except requests.exceptions.ConnectionError:
        flash("Unable to connect to the server. Please check your internet connection.", "danger")
        return redirect(url_for('auth.reset_password'))
    except Exception as e:
        flash("An unexpected error occurred. Please try again later.", "danger")
        return redirect(url_for('auth.reset_password'))


@auth.route('/reset-password', methods=['GET'])
def reset_password():
    return render_template('reset_password.html')