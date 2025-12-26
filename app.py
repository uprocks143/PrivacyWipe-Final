import os, pyotp, sqlite3, requests
from flask import Flask, render_template, request, jsonify, session, redirect

app = Flask(__name__)
app.secret_key = "V3_ULTRA_SECURE_KEY"

# Database upgrade to store verified status
def init_db():
    conn = sqlite3.connect('system.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (identifier TEXT UNIQUE, password TEXT, verified INTEGER DEFAULT 0)')
    conn.close()

init_db()

# --- OTP SYSTEM ---
totp = pyotp.TOTP('BASE32SECRET3232') # Demo ke liye

@app.route('/send_otp', methods=['POST'])
def send_otp():
    target = request.json.get('target') # Email or Phone
    otp = totp.now()
    # Yahan aapka Email/SMS API code aayega (Jaise Twilio ya SendGrid)
    print(f"[SYSTEM] Sending OTP {otp} to {target}") 
    session['temp_target'] = target
    session['current_otp'] = otp
    return jsonify({"status": "SENT"})

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

# --- GOOGLE LOGIN (Button Work Logic) ---
@app.route('/login/google')
def google_auth():
    # Ye user ko Google login page par bhejega
    # Iske liye aapko Google Console se Redirect URI setup karni hogi
    # For now, ye automatic session set karke redirect karega (Demo)
    session['logged_in'] = True
    session['username'] = "google_user@gmail.com"
    return redirect('/')

