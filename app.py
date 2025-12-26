
import os, threading, requests, sqlite3
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from PIL import Image
from PIL.ExifTags import TAGS

app = Flask(__name__)
app.secret_key = "PRIVACY_WIPE_v3_CORE"

# --- CONFIGURATION ---
RAPID_API_KEY = "522355692dmshf7a8225594fd889p1c6510jsnf71a4cabdbcc"
GOOGLE_CLIENT_ID = "YOUR_CLIENT_ID.apps.googleusercontent.com" # Dashboard se mil jayega

def init_db():
    conn = sqlite3.connect('system.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT UNIQUE, password TEXT, hint TEXT)')
    conn.close()

init_db()

@app.route('/')
def index():
    if not session.get('logged_in'): return render_template('login.html')
    return render_template('dashboard.html')

# --- v3.0 AUTH SYSTEM ---
@app.route('/login', methods=['POST'])
def login():
    u, p = request.form.get('username'), request.form.get('password')
    conn = sqlite3.connect('system.db')
    user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
    conn.close()
    if user:
        session['logged_in'], session['username'] = True, u
        return redirect('/')
    return "INVALID_CREDENTIALS", 401

@app.route('/signup', methods=['POST'])
def signup():
    u, p, h = request.form.get('username'), request.form.get('password'), request.form.get('hint')
    conn = sqlite3.connect('system.db')
    try:
        conn.execute("INSERT INTO users VALUES (?, ?, ?)", (u, p, h))
        conn.commit()
        session['logged_in'], session['username'] = True, u
        return redirect('/')
    except: return "USER_ALREADY_EXISTS", 400
    finally: conn.close()

# --- v3.0 CORE TOOLS ---
@app.route('/api/osint', methods=['POST'])
def osint_api():
    target = request.json.get('query')
    found = []
    # Sites.txt logic
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
    return jsonify(requests.get(url, headers=headers).json())

@app.route('/api/exploit', methods=['GET'])
def exploit_api():
    url = "https://exploitdb-dorks-papers-shellcodes.p.rapidapi.com/v1/exploits_code_injection"
    headers = {"x-rapidapi-key": RAPID_API_KEY, "x-rapidapi-host": "exploitdb-dorks-papers-shellcodes.p.rapidapi.com"}
    return jsonify(requests.get(url, headers=headers).json()[:5])

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
