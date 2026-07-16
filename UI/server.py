# File: X:\Corey\UI\server.py
import os
import sys
import logging
from flask import Flask, send_from_directory, jsonify

app = Flask(__name__, static_folder=".")

# Suppress annoying requests spam in terminal
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route("/")
def index():
    # Serves the UI directly from X:\Corey\UI\index.html
    return send_from_directory(os.path.dirname(__file__), "index.html")

# --- COREY API ENDPOINTS ---
@app.route("/api/weather")
def api_weather():
    # Put your local Corey weather logic here
    return jsonify({"location": "North Nazimabad", "temp": "32°C", "sky": "Clear"})

@app.route("/api/system")
def api_system():
    # Put your local Corey hardware tracking logic here
    return jsonify({"cpu": "12%", "ram": "48%", "status": "online"})

if __name__ == "__main__":
    print("[*] Starting Corey Local Engine...")
    print("👉 Running on: http://127.0.0.1:5000")
    app.run(port=5000, host="127.0.0.1")