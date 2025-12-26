
import os, threading, requests, sqlite3
from flask import Flask, render_template, request, jsonify, session, redirect
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

app = Flask(__name__)
app.secret_key = "CYBER_WIPE_SECRET_99"

# API Configuration
RAPID_API_KEY = "522355692dmshf7a8225594fd889p1c6510jsnf71a4cabdbcc"

# Database Init
def init_db():
    conn = sqlite3.connect('system.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT, hint TEXT)')
    conn.close()

init_db()

@app.route('/')
def index():
    if not session.get('logged_in'): return render_template('login.html')
    return render_template('dashboard.html')

# --- AUTH LOGIC ---
@app.route('/login', methods=['POST'])
def login():
    u, p = request.form.get('username'), request.form.get('password')
    conn = sqlite3.connect('system.db')
    user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
    conn.close()
    if user:
        session['logged_in'], session['username'] = True, u
        return redirect('/')
    return "AUTH_FAILED", 401

@app.route('/signup', methods=['POST'])
def signup():
    u, p, h = request.form.get('username'), request.form.get('password'), request.form.get('hint')
    conn = sqlite3.connect('system.db')
    try:
        conn.execute("INSERT INTO users VALUES (?, ?, ?)", (u, p, h))
        conn.commit()
        return redirect('/')
    except: return "ERROR", 400
    finally: conn.close()

# --- REAL OSINT SCAN ---
def check_site(url, found):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if r.status_code == 200: found.append(url)
    except: pass

@app.route('/api/osint', methods=['POST'])
def osint_api():
    target = request.json.get('query')
    found = []
    with open('sites.txt', 'r') as f:
        sites = [line.strip() for line in f.readlines()[:50]]
    threads = [threading.Thread(target=check_site, args=(f"https://{s}/{target}", found)) for s in sites]
    for t in threads: t.start()
    for t in threads: t.join()
    return jsonify({"status": "SUCCESS", "found": found})

# --- BREACH & EXPLOIT APIs ---
@app.route('/api/breach', methods=['POST'])
def breach_api():
    email = request.json.get('email')
    url = "https://breachdirectory.p.rapidapi.com/"
    headers = {"x-rapidapi-key": RAPID_API_KEY, "x-rapidapi-host": "breachdirectory.p.rapidapi.com"}
    res = requests.get(url, headers=headers, params={"func": "auto", "term": email})
    return jsonify(res.json())

@app.route('/api/exploit', methods=['GET'])
def exploit_api():
    url = "https://exploitdb-dorks-papers-shellcodes.p.rapidapi.com/v1/exploits_code_injection"
    headers = {"x-rapidapi-key": RAPID_API_KEY, "x-rapidapi-host": "exploitdb-dorks-papers-shellcodes.p.rapidapi.com"}
    res = requests.get(url, headers=headers)
    return jsonify(res.json()[:10])

# --- FORENSIC BACKTRACK ---
@app.route('/api/forensic', methods=['POST'])
def forensic_api():
    file = request.files['file']
    path = "temp.jpg"
    file.save(path)
    img = Image.open(path)
    report = {"Format": img.format, "Size": f"{img.width}x{img.height}"}
    exif = img._getexif()
    if exif:
        for tag, val in exif.items():
            tag_name = TAGS.get(tag, tag)
            report[tag_name] = str(val)
    os.remove(path)
    return jsonify(report)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
