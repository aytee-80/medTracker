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

        # Client-side validation missed? Catch it here
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
            # Extract meaningful error message from Supabase
            error_msg = data.get('msg') or data.get('error_description') or data.get('error', 'Registration failed')
            
            # Handle specific Supabase errors
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
            
            # Improve error messaging
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
    Returns JSON with success message or detailed error for frontend display.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON", "user_message": "Invalid request format"}), 400

        new_password = data.get("password")
        access_token = data.get("access_token")

        if not access_token:
            return jsonify({"error": "Missing access_token", "user_message": "Session expired. Please request a new reset link."}), 400
        
        if not new_password or len(new_password) < 8:
            return jsonify({"error": "Password too short", "user_message": "Password must be at least 8 characters"}), 400

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
            return jsonify({"message": "Password updated successfully"}), 200

        # Parse Supabase error and create user-friendly message
        try:
            error_details = res.json()
        except:
            error_details = {"raw_response": res.text}

        # Extract and format error message for user
        raw_error = error_details.get('msg') or error_details.get('error_description') or error_details.get('error') or str(error_details)
        
        user_message = "Failed to update password. Please try again."
        
        # Handle specific Supabase password policy errors
        if 'password' in raw_error.lower():
            if 'similar' in raw_error.lower():
                user_message = "New password cannot be similar to your previous password. Please choose a more different password."
            elif 'weak' in raw_error.lower() or 'strength' in raw_error.lower():
                user_message = "Password does not meet security requirements. Use at least 8 characters with letters, numbers, and symbols."
            elif 'previously used' in raw_error.lower():
                user_message = "You cannot reuse a previous password. Please choose a new password."
            elif 'pwned' in raw_error.lower() or 'common' in raw_error.lower():
                user_message = "This password is too common or compromised. Please choose a stronger password."

        return jsonify({
            "error": "Failed to update password",
            "details": error_details,
            "user_message": user_message
        }), res.status_code

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Request timeout",
            "user_message": "The request took too long. Please check your connection and try again."
        }), 504
    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "Connection error",
            "user_message": "Unable to connect to the server. Please check your internet connection."
        }), 503
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "user_message": "An unexpected error occurred. Please try again later."
        }), 500


@auth.route('/reset-password', methods=['GET'])
def reset_password():
    return render_template('reset_password.html')