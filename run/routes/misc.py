from flask import Blueprint, render_template, redirect, url_for, session

misc = Blueprint('misc', __name__)

@misc.route('/education')
def education():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))
    return render_template('education.html')
#safety
@misc.route('/safety')
def safety():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))
    return render_template('safety.html')