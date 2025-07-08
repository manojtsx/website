import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
import google.generativeai as genai
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    raise EnvironmentError("API key not found. Please set the GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")

# Use a global chat session for now (can be improved for multi-user)
model = genai.GenerativeModel("gemini-1.5-flash")
chat = model.start_chat()

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    # System instruction for Gemini to always return JSON with html and css
    system_instruction = (
        "You are a website design generator. "
        "Given a user prompt, generate the HTML and CSS code for the described design. "
        "Respond ONLY with a JSON object in the following format: "
        "{\"html\": \"<html code>\", \"css\": \"<css code>\"}. "
        "Do not include any explanations or extra text."
    )
    full_prompt = f"{system_instruction}\nUser prompt: {prompt}"

    response = chat.send_message(full_prompt)
    print(response.text)

    # Try to parse the response as JSON
    import json
    try:
        text = response.text.strip()
        # Remove code fences if present
        if text.startswith('```json'):
            text = text[len('```json'):].strip()
        if text.startswith('```'):
            text = text[len('```'):].strip()
        if text.endswith('```'):
            text = text[:-3].strip()
        # Try to extract JSON object if extra text is present
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        if first_brace != -1 and last_brace != -1:
            text = text[first_brace:last_brace + 1]
        result = json.loads(text)
        html = result.get('html', '')
        css = result.get('css', '')
    except Exception:
        # Fallback: return raw text if parsing fails
        return jsonify({'error': 'Model did not return valid JSON', 'raw': response.text}), 500

    return jsonify({'html': html, 'css': css})

if __name__ == '__main__':
    app.run(debug=True) 