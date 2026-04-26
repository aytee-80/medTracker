from groq import Groq
import config

# Initialize Groq client (OpenAI-compatible)
client = Groq(api_key=config.GROQ_API_KEY)
AI_MODEL = "llama-3.1-8b-instant"  # Fast, free, good quality
DEMO_MODE = getattr(config, 'AI_DEMO_MODE', False)

# Demo fallback responses
DEMO_RESPONSES = {
    "symptoms": """🔍 **Sample Analysis (Demo Mode)**
**Possible Conditions:** Mild viral infection, tension headache, or dehydration.
**Recommendations:** Rest, hydrate, monitor temperature. OTC pain relief if appropriate.
**When to see a doctor:** Fever >38.5°C for 3+ days, severe pain, confusion, or breathing difficulty.
⚠️ *This is a demo response. Not medical advice.*""",
    "image": """📷 **Image Analysis (Demo Mode)**
Observes skin irritation/rash pattern. Could be contact dermatitis, eczema, or heat rash.
Keep area clean, avoid scratching, consider hydrocortisone cream.
Seek care if spreading, painful, or accompanied by fever.
⚠️ *Image analysis is not a substitute for professional diagnosis.*""",
    "medication": """💊 **Medication Info (Demo Mode) - Ibuprofen**
Uses: Pain relief, fever reduction, anti-inflammatory.
Dosage: 200-400mg every 4-6h (max 1200mg/day OTC).
Side Effects: Stomach upset, dizziness.
⚠️ Avoid if allergic to NSAIDs, pregnant, or have stomach/kidney issues.
Always follow professional medical guidance.""",
    "chat": "👋 Hello! I'm your AI health assistant (Demo Mode). I can help with symptom questions, medication info, and general health tips. Remember: I'm for informational purposes only. What can I help you with?"
}

def analyze_symptoms(symptoms: str, age: int = None, gender: str = None) -> dict:
    if DEMO_MODE:
        return {"success": True, "analysis": DEMO_RESPONSES["symptoms"], "demo": True}
    try:
        prompt = f"""You are a helpful medical assistant. Analyze these symptoms:
Age: {age or 'Not specified'}, Gender: {gender or 'Not specified'}
Symptoms: {symptoms}
Provide: 1) Possible conditions (3-5) 2) OTC recommendations (if appropriate) 3) When to see a doctor 4) Home care tips
Format with clear bullet points. ALWAYS include a disclaimer that this is NOT professional medical advice."""
        
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "You are a knowledgeable medical assistant. Provide clear, structured, and conservative health information. Always emphasize consulting a healthcare professional."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        return {"success": True, "analysis": response.choices[0].message.content}
    except Exception as e:
        print(f"⚠️ Groq fallback: {e}")
        return {"success": True, "analysis": DEMO_RESPONSES["symptoms"], "fallback": True}

def analyze_image(image_file, symptoms_description: str = "") -> dict:
    if DEMO_MODE:
        return {"success": True, "analysis": DEMO_RESPONSES["image"], "demo": True}
    try:
        # Groq vision model for image analysis
        image_bytes = image_file.read()
        import base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        prompt = f"""Analyze this medical image carefully. Provide:
1. Description of what you observe
2. Possible conditions this could indicate
3. Severity assessment (mild/moderate/severe)
4. Recommended actions
5. When to seek immediate medical attention
Additional symptoms: {symptoms_description or 'None provided'}
ALWAYS include a medical disclaimer."""
        
        response = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",  # Vision-capable model
            messages=[
                {"role": "system", "content": "You are a medical image analysis assistant. Provide careful, conservative assessments."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=800
        )
        return {"success": True, "analysis": response.choices[0].message.content}
    except Exception as e:
        print(f"⚠️ Groq fallback (image): {e}")
        return {"success": True, "analysis": DEMO_RESPONSES["image"], "fallback": True}

def get_medication_info(medication_name: str) -> dict:
    if DEMO_MODE:
        return {"success": True, "info": DEMO_RESPONSES["medication"], "demo": True}
    try:
        prompt = f"""Provide comprehensive information about: {medication_name}
Include: 1) Uses/indications 2) Common dosages 3) Side effects 4) Contraindications 5) Drug interactions 6) Special precautions
Format clearly. ALWAYS state this is for informational purposes only."""
        
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "You are a pharmaceutical information specialist."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800
        )
        return {"success": True, "info": response.choices[0].message.content}
    except Exception as e:
        print(f"⚠️ Groq fallback (medication): {e}")
        return {"success": True, "info": DEMO_RESPONSES["medication"], "fallback": True}

def chat_with_ai(message: str, conversation_history: list = None) -> dict:
    if DEMO_MODE:
        return {"success": True, "response": DEMO_RESPONSES["chat"], "demo": True}
    try:
        system_prompt = """You are a helpful medical assistant. You can:
- Answer questions about symptoms and conditions
- Provide information about medications
- Offer general health advice
- Help users understand when to see a doctor
Always be empathetic, clear, and emphasize consulting healthcare professionals. Never diagnose definitively."""
        
        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history[-8:])
        messages.append({"role": "user", "content": message})
        
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=600
        )
        
        return {
            "success": True,
            "response": response.choices[0].message.content,
            "new_message": {"role": "assistant", "content": response.choices[0].message.content}
        }
    except Exception as e:
        print(f"⚠️ Groq fallback (chat): {e}")
        return {"success": True, "response": DEMO_RESPONSES["chat"], "fallback": True}