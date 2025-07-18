import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from groq import Groq, GroqError
import requests
from requests.exceptions import RequestException
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.route('/health')
def health_check():
    return jsonify({
        "status": "OK",
        "groq_ready": bool(os.getenv("GROQ_API_KEY")),
        "python_version": sys.version
    })

# Configuration
class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
    MODELS = {
        "llama3-8b-8192": "Llama 3 8B (Fast)",
        "llama3-70b-8192": "Llama 3 70B (Powerful)"
    }
    DEFAULT_MODEL = "llama3-8b-8192"

# Initialize Groq client with error handling
def get_groq_client():
    """Initialize and return authenticated Groq client"""
    if not Config.GROQ_API_KEY:
        logger.error("GROQ_API_KEY not found in environment variables")
        raise ValueError("API key not configured")
    
    try:
        return Groq(api_key=Config.GROQ_API_KEY)
    except GroqError as e:
        logger.error(f"Groq client initialization failed: {str(e)}")
        raise

@app.route('/')
def home():
    """Render main page with current time"""
    try:
        return render_template(
            'index.html',
            models=Config.MODELS,
            current_time=datetime.now().strftime("%H:%M")
        )
    except Exception as e:
        logger.error(f"Home route error: {str(e)}")
        return render_template('error.html'), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests with Groq API"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'status': 'error', 'message': 'Invalid request'}), 400
            
        client = get_groq_client()
        
        messages = [{
            "role": "system",
            "content": "You are a helpful AI assistant. Be friendly and concise."
        }]
        
        if 'history' in data:
            messages.extend(data['history'])
        
        messages.append({
            "role": "user", 
            "content": data['message']
        })
        
        response = client.chat.completions.create(
            messages=messages,
            model=data.get('model', Config.DEFAULT_MODEL),
            temperature=0.7,
            max_tokens=4000
        )
        
        return jsonify({
            'status': 'success',
            'response': response.choices[0].message.content,
            'timestamp': datetime.now().strftime("%H:%M")
        })
        
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except GroqError as e:
        return jsonify({'status': 'error', 'message': f"API error: {str(e)}"}), 502
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.route('/weather', methods=['POST'])
def weather():
    """Handle weather data requests"""
    try:
        data = request.get_json()
        location = data.get('location')
        
        if not location:
            return jsonify({'status': 'error', 'message': 'Location required'}), 400
            
        params = {
            'q': location,
            'appid': Config.OPENWEATHER_API_KEY,
            'units': 'metric',
            'lang': 'id'
        }
        
        response = requests.get(Config.WEATHER_URL, params=params, timeout=10)
        response.raise_for_status()
        weather_data = response.json()
        
        return jsonify({
            'status': 'success',
            'data': {
                'location': f"{weather_data['name']}, {weather_data['sys']['country']}",
                'temp': round(weather_data['main']['temp']),
                'feels_like': round(weather_data['main']['feels_like']),
                'description': weather_data['weather'][0]['description'].capitalize(),
                'icon': weather_data['weather'][0]['icon'],
                'humidity': weather_data['main']['humidity'],
                'wind': round(weather_data['wind']['speed'] * 3.6, 1)
            }
        })
        
    except RequestException as e:
        logger.error(f"Weather API error: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Weather service unavailable'}), 502
    except KeyError as e:
        logger.error(f"Data parsing error: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Invalid weather data'}), 502
    except Exception as e:
        logger.error(f"Weather error: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port)  # Wajib untuk Northflank
