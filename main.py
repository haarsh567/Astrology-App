from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
import bcrypt
import requests
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the Google Gemini API key from the environment variables
google_api_key = os.getenv("GOOGLE_API_KEY")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static'  # Path to your static folder

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["login"]  # Assuming "login" is the name of the database
users_collection = db["data"]  # Assuming "data" is the name of the collection

# Function to hash the password
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed

# Function to handle user login
def login(username, password):
    # Retrieve user from database
    user = users_collection.find_one({"username": username})
    if user:
        # Validate password
        if bcrypt.checkpw(password.encode('utf-8'), user["password"]):
            return True
    return False

# Function to handle user registration
def register(username, password):
    # Check if username already exists
    if users_collection.find_one({"username": username}) is None:
        # Hash the password
        hashed_password = hash_password(password)
        # Store user in the database
        users_collection.insert_one({"username": username, "password": hashed_password})

# Initialize the Gemini API endpoint URL
gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={google_api_key}"

# Function to handle Gemini AI chat with different prompts
def gemini_chat(prompt):
    payload = {
        'contents': [{
            'parts': [{
                'text': prompt
            }]
        }]
    }
    response = requests.post(gemini_api_url, json=payload)

    if response.status_code == 200:
        return response.json().get('candidates')[0]['content']['parts'][0]['text']
    else:
        return "Error: Unable to fetch Gemini AI response"

# Route for the login page
@app.route('/', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        action = request.form['action']

        if action == 'Login':
            if login(username, password):
                return redirect(url_for('horoscope_form'))
            else:
                error = "Invalid username or password"
                return render_template('login.html', error=error)
        else:
            register(username, password)
            return redirect(url_for('horoscope_form'))

    return render_template('login.html')

# Route for the horoscope form
@app.route('/horoscope-form')
def horoscope_form():
    return render_template('prediction.html')

# Route for the horoscope prediction
@app.route('/horoscope-prediction', methods=['POST'])
def horoscope_prediction():
    if request.method == 'POST':
        data = request.json
        birth_date = data.get('birth_date')
        birth_time = data.get('birth_time')
        birth_location = data.get('birth_location')

        # Construct prompt for horoscope prediction
        prompt = f"Generate horoscope for a person born on {birth_date} at {birth_time} in {birth_location}."

        # Get response from Gemini AI
        response = gemini_chat(prompt)

        return jsonify({"prediction": response})

# Route for handling user messages and interacting with Gemini AI
@app.route('/gemini-chat', methods=['POST'])
def gemini_chat_route():
    if request.method == 'POST':
        message = request.json.get('message')
        prompt = ""

        # Determine prompt based on user message
        if "marriage" in message:
            prompt = "Provide marriage details according to birth date, time, and place."
        elif "career" in message:
            prompt = "Provide career guidance according to birth date, time, and place."
        elif "health" in message:
            prompt = "Provide health life details according to birth date, time, and place."
        elif "negative" in message:
            prompt = "Provide negative influences according to birth place, time, and date."
        else:
            prompt = "Provide a response to the user query."

        # Get response from Gemini AI
        response = gemini_chat(prompt)

        return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
