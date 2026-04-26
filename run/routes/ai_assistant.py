from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
import os
from run.services.ai_service import (
    analyze_symptoms, 
    analyze_image, 
    get_medication_info,
    chat_with_ai
)

ai_assistant = Blueprint('ai_assistant', __name__, url_prefix='/ai')

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@ai_assistant.route('/')
def ai_home():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))
    return render_template('ai_home.html')

@ai_assistant.route('/symptom_checker')
def symptom_checker():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))
    return render_template('symptom_checker.html')

@ai_assistant.route('/analyze_symptoms', methods=['POST'])
def analyze_symptoms_route():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    data = request.json
    symptoms = data.get('symptoms', '')
    age = data.get('age')
    gender = data.get('gender')
    
    if not symptoms:
        return jsonify({"success": False, "error": "No symptoms provided"})
    
    result = analyze_symptoms(symptoms, age, gender)
    return jsonify(result)

@ai_assistant.route('/image_analysis')
def image_analysis():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))
    return render_template('image_analysis.html')

@ai_assistant.route('/upload_image', methods=['POST'])
def upload_image():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    if 'image' not in request.files:
        return jsonify({"success": False, "error": "No image uploaded"}), 400
    
    file = request.files['image']
    symptoms = request.form.get('symptoms', '')
    
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400
    
    if file and allowed_file(file.filename):
        result = analyze_image(file, symptoms)
        return jsonify(result)
    else:
        return jsonify({"success": False, "error": "Invalid file type. Use PNG, JPG, or GIF."}), 400

@ai_assistant.route('/medication_info')
def medication_info_page():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))
    return render_template('medication_info.html')

@ai_assistant.route('/get_medication_info', methods=['POST'])
def get_medication_info_route():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    data = request.json
    medication_name = data.get('medication_name', '')
    
    if not medication_name:
        return jsonify({"success": False, "error": "No medication name provided"})
    
    result = get_medication_info(medication_name)
    return jsonify(result)

@ai_assistant.route('/chat')
def chat_page():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))
    return render_template('ai_chat.html')

@ai_assistant.route('/chat/send', methods=['POST'])
def chat_send():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    data = request.json
    message = data.get('message', '')
    
    if not message:
        return jsonify({"success": False, "error": "No message provided"})
    
    # Get conversation history from session
    conversation_history = session.get('ai_conversation', [])
    
    result = chat_with_ai(message, conversation_history)
    
    if result['success']:
        # Update conversation history
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append(result['new_message'])
        session['ai_conversation'] = conversation_history
        session.modified = True
    
    return jsonify(result)

@ai_assistant.route('/chat/clear')
def clear_chat():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))
    
    session.pop('ai_conversation', None)
    return redirect(url_for('ai_assistant.chat_page'))