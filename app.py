from flask import Flask, jsonify, send_from_directory
import requests
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# ----------------- CONFIG -----------------
CLIENT_ID = os.getenv("CLIENT_ID", "a9nabo03iqzc4bcbypwc8ja6nh5u2d")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "3ajonemow3s2vn54harwqh2a9qterb")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "").strip()
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN", "").strip()
USER_ID = os.getenv("USER_ID", "753095247")
# -----------------------------------------


# ------------ TOKEN REFRESH --------------
def refresh_access_token():
    global ACCESS_TOKEN, REFRESH_TOKEN
    url = "https://id.twitch.tv/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    r = requests.post(url, data=data)
    if r.status_code != 200:
        logging.error("Error refrescando token: %s %s", r.status_code, r.text)
        return False

    resp = r.json()
    ACCESS_TOKEN = resp.get("access_token")
    REFRESH_TOKEN = resp.get("refresh_token", REFRESH_TOKEN)

    logging.info("🔄 Token actualizado automáticamente")
    return True


def get_headers():
    return {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }


def safe_request(url):
    r = requests.get(url, headers=get_headers())

    # Si el token ha expirado
    if r.status_code == 401:
        logging.info("⚠️ Token expirado, refrescando...")
        if refresh_access_token():
            r = requests.get(url, headers=get_headers())

    return r


# ------------ TWITCH API CALLS -----------
def get_user_info():
    url = "https://api.twitch.tv/helix/users"
    r = safe_request(url)
    if r.status_code != 200:
        logging.error("Error users: %s %s", r.status_code, r.text)
        return None

    data = r.json()
    return data.get('data', [{}])[0] if data.get('data') else None


def get_followers():
    url = f"https://api.twitch.tv/helix/channels/followers?broadcaster_id={USER_ID}"
    r = safe_request(url)
    if r.status_code != 200:
        logging.error("Error followers: %s %s", r.status_code, r.text)
        return 0
    return r.json().get("total", 0)


def get_stream_info():
    url = f"https://api.twitch.tv/helix/streams?user_id={USER_ID}"
    r = safe_request(url)
    if r.status_code != 200:
        logging.error("Error streams: %s %s", r.status_code, r.text)
        return None

    data = r.json()
    return data.get('data', [{}])[0] if data.get('data') else None


# ------------ API ROUTE ------------------
@app.route("/api/status")
def api_status():
    user = get_user_info()
    followers = get_followers()
    stream = get_stream_info()

    info = {
        "display_name": user.get("display_name") if user else "-",
        "login": user.get("login") if user else "-",
        "user_id": user.get("id") if user else "-",
        "views_total": user.get("view_count", 0) if user else 0,
        "followers": followers,
        "stream_online": bool(stream),
        "title": stream.get("title", "-") if stream else "-",
        "viewer_count": stream.get("viewer_count", 0) if stream else 0,
        "profile_image_url": user.get("profile_image_url", "") if user else ""
    }

    return jsonify(info)


# ------------ FRONTEND --------------------
@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard prend0</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #0e0e10;
                color: #efeff1;
                padding: 30px;
            }
            .card {
                background: #18181b;
                padding: 20px;
                border-radius: 10px;
                width: 350px;
                margin-bottom: 20px;
                box-shadow: 0 0 10px #00000055;
            }
            h1 { color: #9146FF; }
            .avatar {
                width: 80px;
                height: 80px;
                border-radius: 50%;
                border: 3px solid #9146FF;
            }
        </style>
    </head>
    <body>

        <h1>Dashboard prend0</h1>

        <div class="card">
            <img id="avatar" class="avatar" src="" />
            <h2 id="display_name">-</h2>
            <p><b>Login:</b> <span id="login">-</span></p>
            <p><b>Seguidores:</b> <span id="followers">0</span></p>
            <p><b>Viewers:</b> <span id="viewer_count">0</span></p>
            <p><b>En directo:</b> <span id="stream_online">No</span></p>
        </div>

        <p style="color:#555;">Actualiza cada 10 segundos</p>

        <script>
            async function update() {
                const res = await fetch("/api/status");
                const data = await res.json();

                document.getElementById("avatar").src = data.profile_image_url;
                document.getElementById("display_name").textContent = data.display_name;
                document.getElementById("login").textContent = data.login;
                document.getElementById("followers").textContent = data.followers;
                document.getElementById("viewer_count").textContent = data.viewer_count;
                document.getElementById("stream_online").textContent = data.stream_online ? "Sí" : "No";
            }

            update();
            setInterval(update, 10000);
        </script>

    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(debug=True)
