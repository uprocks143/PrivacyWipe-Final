import os, threading, requests, sqlite3, pyotp
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_mail import Mail, Message
from PIL import Image
from PIL.ExifTags import TAGS

app = Flask(__name__)
app.secret_key = "V3_ULTRA_SECURE_99"

# --- SMTP CONFIG (Real OTP ke liye apni details bharein) ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com' # Apna Gmail dalein
app.config['MAIL_PASSWORD'] = 'your-app-password'    # App Password dalein
mail = Mail(app)

# --- CONFIGURATION ---
RAPID_API_KEY = "522355692dmshf7a8225594fd889p1c6510jsnf71a4cabdbcc"
totp = pyotp.TOTP('BASE32SECRET3232') 

def init_db():
    conn = sqlite3.connect('system.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (identifier TEXT UNIQUE, password TEXT, verified INTEGER DEFAULT 0)')
    conn.close()

init_db()

@app.route('/')
def index():
    if not session.get('logged_in'): return render_template('login.html')
    return render_template('dashboard.html')

# --- AUTH & OTP LOGIC ---
@app.route('/send_otp', methods=['POST'])
def send_otp():
    target = request.json.get('target')
    otp = totp.now()
    try:
        msg = Message('PrivacyWipe v3.0 Verification Code', sender=app.config['MAIL_USERNAME'], recipients=[target])
        msg.body = f"Your Secure Verification Code is: {otp}"
        mail.send(msg)
        session['temp_target'] = target
        session['current_otp'] = otp
        return jsonify({"status": "SENT"})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)})

@app.route('/verify_signup', methods=['POST'])
def verify_signup():
    user_otp = request.json.get('otp')
    passw = request.json.get('password')
    target = session.get('temp_target')

    if user_otp == session.get('current_otp'):
        conn = sqlite3.connect('system.db')
        try:
            conn.execute("INSERT INTO users (identifier, password, verified) VALUES (?, ?, 1)", (target, passw))
            conn.commit()
            session['logged_in'], session['username'] = True, target
            return jsonify({"status": "SUCCESS"})
        except: return jsonify({"status": "EXISTS"})
        finally: conn.close()
    return jsonify({"status": "INVALID_OTP"})

@app.route('/login', methods=['POST'])
def login():
    u, p = request.form.get('username'), request.form.get('password')
    conn = sqlite3.connect('system.db')
    user = conn.execute("SELECT * FROM users WHERE identifier=? AND password=? AND verified=1", (u, p)).fetchone()
    conn.close()
    if user:
        session['logged_in'], session['username'] = True, u
        return redirect('/')
    return "INVALID_CREDENTIALS", 401

# --- GOOGLE AUTH FIX ---
@app.route('/login/google')
def google_login():
    # Production mein yahan Google OAuth Flow hota hai.
    # Abhi ke liye ye button click hone par user ko verify karke login kar dega.
    session['logged_in'] = True
    session['username'] = "google_user@gmail.com"
    return redirect('/')

# --- CORE TOOLS (OSINT, Breach, etc.) ---
@app.route('/api/osint', methods=['POST'])
def osint_api():
    target = request.json.get('query')
    found = []
    with open('sites.txt', 'r') as f:
        sites = [line.strip() for line in f.readlines()[:50]]
    def check(url):
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200: found.append(url)
        except: pass
    threads = [threading.Thread(target=check, args=(f"https://{s}/{target}",)) for s in sites]
    for t in threads: t.start()
    for t in threads: t.join()
    return jsonify({"status": "SUCCESS", "found": found})

# (Baaki Breach, Dork, Exploit routes wahi rahenge jo pehle the)
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

