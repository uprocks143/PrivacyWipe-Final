import os, threading, requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from PIL import Image
from PIL.ExifTags import TAGS

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "SUPER_SECRET_KEY")

# --- CONFIGURATION ---
RAPID_API_KEY = "522355692dmshf7a8225594fd889p1c6510jsnf71a4cabdbcc"

# Google Config
CLIENT_CONFIG = {
    "web": {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}
SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'openid', 'https://www.googleapis.com/auth/userinfo.email']

@app.route('/')
def index():
    # Ab ye check karega: Agar login hai to User dikhaye, nahi to Guest
    is_logged_in = 'credentials' in session
    user_email = session.get('user_email', 'GUEST_USER')
    # IMPORTANT: Sirf dashboard.html render hoga
    return render_template('dashboard.html', logged_in=is_logged_in, user=user_email)

# --- GOOGLE AUTH FLOW ---
@app.route('/auth/google')
def google_auth():
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES)
    flow.redirect_uri = url_for('callback', _external=True)
    authorization_url, state = flow.authorization_url(access_type='offline')
    session['state'] = state
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES, state=session['state'])
    flow.redirect_uri = url_for('callback', _external=True)
    flow.fetch_token(authorization_response=request.url)
    
    creds = flow.credentials
    session['credentials'] = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }
    
    service = build('oauth2', 'v2', credentials=creds)
    user_info = service.userinfo().get().execute()
    session['user_email'] = user_info['email']
    
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- API ROUTES ---

@app.route('/api/osint', methods=['POST'])
def osint_real():
    target = request.json.get('target')
    found_urls = []
    # Sites.txt check
    try:
        with open('sites.txt', 'r') as f:
            sites = [line.strip() for line in f.readlines()[:50]]
    except:
        sites = ["instagram.com", "facebook.com", "twitter.com"]

    def check_url(website):
        try:
            r = requests.get(f"https://{website}/{target}", timeout=3)
            if r.status_code == 200: found_urls.append(f"https://{website}/{target}")
        except: pass

    threads = [threading.Thread(target=check_url, args=(s,)) for s in sites]
    for t in threads: t.start()
    for t in threads: t.join()
    
    return jsonify({"status": "DONE", "results": found_urls})

@app.route('/api/breach', methods=['POST'])
def breach_real():
    email = request.json.get('email')
    url = "https://breachdirectory.p.rapidapi.com/"
    headers = {"x-rapidapi-key": RAPID_API_KEY, "x-rapidapi-host": "breachdirectory.p.rapidapi.com"}
    try:
        res = requests.get(url, headers=headers, params={"func": "auto", "term": email})
        return jsonify(res.json())
    except: return jsonify({"success": False})

@app.route('/api/forensic', methods=['POST'])
def forensic_real():
    if 'file' not in request.files: return jsonify({"error": "No file"})
    file = request.files['file']
    try:
        img = Image.open(file)
        exif = img._getexif()
        meta = {TAGS.get(t, t): str(v) for t, v in exif.items()} if exif else {}
        return jsonify({"meta": meta, "size": img.size, "format": img.format})
    except: return jsonify({"error": "Failed"})

@app.route('/api/wipe', methods=['POST'])
def wipe_protocol():
    if 'credentials' not in session:
        return jsonify({"status": "LOGIN_REQUIRED"}), 200
    return jsonify({"status": "SUCCESS", "message": "Requests Queued"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
