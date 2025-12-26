import os, threading, requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from PIL import Image
from PIL.ExifTags import TAGS

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- CONFIGURATION ---
# RapidAPI Key (Jo aapne di thi)
RAPID_API_KEY = "522355692dmshf7a8225594fd889p1c6510jsnf71a4cabdbcc"

# Google Client Config (Environment Variables se ayega Render pr)
CLIENT_CONFIG = {
    "web": {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID", "YOUR_LOCAL_ID"),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", "YOUR_LOCAL_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}
SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'openid', 'https://www.googleapis.com/auth/userinfo.email']

@app.route('/')
def index():
    # Frontend ko btana ki user logged in hai ya nhi
    is_logged_in = 'credentials' in session
    user_email = session.get('user_email', 'GUEST_USER')
    return render_template('dashboard.html', logged_in=is_logged_in, user=user_email)

# --- GOOGLE AUTH FLOW ---
@app.route('/auth/google')
def google_auth():
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES)
    # Render URL ke hisab se redirect set karein
    redirect_uri = url_for('callback', _external=True)
    flow.redirect_uri = redirect_uri
    
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
    
    # User ka email fetch krna
    service = build('oauth2', 'v2', credentials=creds)
    user_info = service.userinfo().get().execute()
    session['user_email'] = user_info['email']
    
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- FREE TOOLS (OPEN ACCESS) ---

@app.route('/api/osint', methods=['POST'])
def osint_real():
    target = request.json.get('target')
    found_urls = []
    
    # Real Threaded Scan
    def check_url(website):
        try:
            url = f"https://{website}/{target}"
            r = requests.get(url, timeout=3, headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code == 200:
                found_urls.append(url)
        except: pass

    with open('sites.txt', 'r') as f:
        sites = [line.strip() for line in f.readlines()]

    threads = []
    for s in sites:
        t = threading.Thread(target=check_url, args=(s,))
        threads.append(t)
        t.start()
    
    for t in threads: t.join()
    
    return jsonify({"status": "DONE", "results": found_urls})

@app.route('/api/breach', methods=['POST'])
def breach_real():
    email = request.json.get('email')
    url = "https://breachdirectory.p.rapidapi.com/"
    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": "breachdirectory.p.rapidapi.com"
    }
    try:
        res = requests.get(url, headers=headers, params={"func": "auto", "term": email})
        return jsonify(res.json())
    except:
        return jsonify({"success": False})

@app.route('/api/forensic', methods=['POST'])
def forensic_real():
    if 'file' not in request.files: return jsonify({"error": "No file"})
    file = request.files['file']
    try:
        img = Image.open(file)
        exif = img._getexif()
        meta = {}
        if exif:
            for tag, value in exif.items():
                decoded = TAGS.get(tag, tag)
                meta[str(decoded)] = str(value)
        return jsonify({"meta": meta, "size": img.size, "format": img.format})
    except:
        return jsonify({"error": "Failed to parse image"})

# --- RESTRICTED TOOL (LOGIN REQUIRED) ---

@app.route('/api/wipe', methods=['POST'])
def wipe_protocol():
    # Yaha check hoga ki user login hai ya nhi
    if 'credentials' not in session:
        return jsonify({"status": "LOGIN_REQUIRED"}), 401
    
    # Agar login hai, to WIPE start
    # (Real implementation mein yaha Gmail API se mail jayega)
    return jsonify({"status": "SUCCESS", "message": "Authorized! 200,000 Deletion Requests Queued."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
