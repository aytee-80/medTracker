from flask import Blueprint, request, redirect, url_for, session, render_template, flash, jsonify
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

        # Supabase returns 204 No Content on success
        if res.status_code in [200, 204]:
            flash("If an account exists with that email, a password reset link has been sent.", "success")
        else:
            try:
                error_data = res.json()
                flash(f"Error: {error_data.get('error_description', 'Failed to send reset email')}", "danger")
            except:
                flash("Error sending reset email", "danger")

        return redirect(url_for('main.home'))

    return render_template('forgot_password.html')


@auth.route('/update-password', methods=['POST'])
def update_password():
    """
    Handle password update via Supabase Auth API.
    Expects JSON: { "password": "...", "access_token": "...", "refresh_token": "..." }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        new_password = data.get("password")
        access_token = data.get("access_token")

        # Validation
        if not access_token:
            return jsonify({"error": "Missing access_token"}), 400
        if not new_password or len(new_password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400

        # Build headers with recovery access_token
        headers = {
            "apikey": config.SUPABASE_KEY,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Call Supabase Auth API to update password
        # NOTE: Recovery tokens have permission to update user password directly
        res = requests.put(
            f"{config.SUPABASE_URL}/auth/v1/user",
            json={"password": new_password},
            headers=headers,
            timeout=30
        )

        # Log response for debugging (use proper logging in production)
        print(f"[Supabase] Status: {res.status_code}")
        print(f"[Supabase] Response: {res.text}")

        if res.status_code in [200, 204]:
            return jsonify({"message": "Password updated successfully"}), 200

        # Parse and return Supabase error
        try:
            error_details = res.json()
        except:
            error_details = {"raw_response": res.text}

        return jsonify({
            "error": "Failed to update password",
            "details": error_details
        }), res.status_code

    except Exception as e:
        print(f"[ERROR] update_password exception: {str(e)}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@auth.route('/reset-password', methods=['GET'])
def reset_password():
    """
    Render the password reset page.
    The access_token is extracted from the URL hash on the client side.
    """
    return render_template('reset_password.html')