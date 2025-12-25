import os
import sqlite3
import base64
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from PIL import Image
from PIL.ExifTags import TAGS

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('system.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, hint TEXT)''')
    # Default Admin (User: admin, Pass: root123, Hint: secret)
    c.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'root123', 'secret')")
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('login.html')
    return render_template('dashboard.html')

@app.route('/login', methods=['POST'])
def login():
    u, p = request.form.get('username'), request.form.get('password')
    conn = sqlite3.connect('system.db')
    user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
    conn.close()
    if user:
        session['logged_in'] = True
        return redirect('/')
    return "<h1>ACCESS DENIED</h1>", 401

@app.route('/reset-password', methods=['POST'])
def reset():
    u, h, p = request.form.get('username'), request.form.get('hint'), request.form.get('new_pass')
    conn = sqlite3.connect('system.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password=? WHERE username=? AND hint=?", (p, u, h))
    conn.commit()
    updated = cursor.rowcount
    conn.close()
    return "SUCCESS" if updated > 0 else "FAILED"

@app.route('/api/osint', methods=['POST'])
def osint_api():
    query = request.json.get('query')
    # Demo Breach Data
    return jsonify({"status": "EXPOSED", "breaches": ["LinkedIn", "Canva", "Adobe"], "leaks": "Passwords, Emails, IPs"})

@app.route('/api/forensic', methods=['POST'])
def forensic_api():
    file = request.files['image']
    img = Image.open(file)
    exif = img._getexif()
    metadata = {TAGS.get(t, t): str(v) for t, v in exif.items()} if exif else {"Error": "No EXIF Data Found"}
    return jsonify({"metadata": metadata})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
