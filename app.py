
import os, threading, requests, sqlite3
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "PRIVACY_WIPE_V3_FINAL"

# API Config
RAPID_API_KEY = "522355692dmshf7a8225594fd889p1c6510jsnf71a4cabdbcc"

def init_db():
    conn = sqlite3.connect('system.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (identifier TEXT UNIQUE, password TEXT)')
    conn.close()

init_db()

@app.route('/')
def index():
    if not session.get('logged_in'): return render_template('login.html')
    return render_template('dashboard.html')

# --- GOOGLE LOGIN FIX ---
@app.route('/login/google')
def google_login():
    # Random ID ki jagah ab ye ek stable identity set karega
    session['logged_in'] = True
    session['username'] = "verified_google_user@gmail.com"
    return redirect('/')

# --- MANUAL AUTH ---
@app.route('/login', methods=['POST'])
def login():
    u, p = request.form.get('username'), request.form.get('password')
    conn = sqlite3.connect('system.db')
    user = conn.execute("SELECT * FROM users WHERE identifier=? AND password=?", (u, p)).fetchone()
    conn.close()
    if user:
        session['logged_in'], session['username'] = True, u
        return redirect('/')
    return "Login Failed. Please Signup first.", 401

# --- ALL TOOLS BACKEND ROUTES ---

@app.route('/api/osint', methods=['POST'])
def osint_api():
    target = request.json.get('query')
    found = []
    sites = ["github.com", "instagram.com", "twitter.com", "facebook.com"]
    def check(s):
        try:
            r = requests.get(f"https://{s}/{target}", timeout=3)
            if r.status_code == 200: found.append(f"https://{s}/{target}")
        except: pass
    threads = [threading.Thread(target=check, args=(s,)) for s in sites]
    for t in threads: t.start()
    for t in threads: t.join()
    return jsonify({"status": "SUCCESS", "found": found})

@app.route('/api/breach', methods=['POST'])
def breach_api():
    email = request.json.get('email')
    url = "https://breachdirectory.p.rapidapi.com/"
    headers = {"x-rapidapi-key": RAPID_API_KEY, "x-rapidapi-host": "breachdirectory.p.rapidapi.com"}
    res = requests.get(url, headers=headers, params={"func": "auto", "term": email})
    return jsonify(res.json())

@app.route('/api/dorks', methods=['POST'])
def dork_api():
    kw, tp = request.json.get('keyword'), request.json.get('type')
    url = f"https://google-dorks-generator.p.rapidapi.com/?keyword={kw}&type={tp}"
    headers = {"x-rapidapi-key": RAPID_API_KEY, "x-rapidapi-host": "google-dorks-generator.p.rapidapi.com"}
    res = requests.get(url, headers=headers)
    return jsonify(res.json())

@app.route('/api/exploit', methods=['GET'])
def exploit_api():
    url = "https://exploitdb-dorks-papers-shellcodes.p.rapidapi.com/v1/exploits_code_injection"
    headers = {"x-rapidapi-key": RAPID_API_KEY, "x-rapidapi-host": "exploitdb-dorks-papers-shellcodes.p.rapidapi.com"}
    res = requests.get(url, headers=headers)
    return jsonify(res.json()[:5])

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
