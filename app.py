from flask import Flask, jsonify, render_template
import requests
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# ----------------- TWITCH CONFIG -----------------
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
USER_ID = os.getenv("USER_ID")

# ----------------- YOUTUBE CONFIG -----------------
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")

# =====================================================
# ===============  TWITCH FUNCTIONS  ==================
# =====================================================

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
    return True

def get_headers():
    return {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

def safe_request(url):
    r = requests.get(url, headers=get_headers())
    if r.status_code == 401:
        if refresh_access_token():
            r = requests.get(url, headers=get_headers())
    return r

def get_twitch_user():
    url = "https://api.twitch.tv/helix/users"
    return safe_request(url).json().get("data", [{}])[0]

def get_twitch_followers():
    url = f"https://api.twitch.tv/helix/channels/followers?broadcaster_id={USER_ID}"
    r = safe_request(url)
    return r.json().get("total", 0)

def get_twitch_stream():
    url = f"https://api.twitch.tv/helix/streams?user_id={USER_ID}"
    data = safe_request(url).json()
    return data.get("data", [{}])[0] if data.get("data") else None


@app.route("/api/twitch")
def api_twitch():
    user = get_twitch_user()
    followers = get_twitch_followers()
    stream = get_twitch_stream()

    info = {
        "display_name": user.get("display_name", "-"),
        "login": user.get("login", "-"),
        "followers": followers,
        "views_total": user.get("view_count", 0),
        "stream_online": bool(stream),
        "viewer_count": stream.get("viewer_count", 0) if stream else 0,
        "title": stream.get("title", "-") if stream else "-"
    }
    return jsonify(info)

# =====================================================
# ===============  YOUTUBE FUNCTIONS  =================
# =====================================================

def yt_request(url, params):
    params["key"] = YOUTUBE_API_KEY
    return requests.get(url, params=params).json()

def get_yt_channel_stats():
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "id": YOUTUBE_CHANNEL_ID,
        "part": "statistics,snippet"
    }
    data = yt_request(url, params)
    if "items" not in data:
        return None
    return data["items"][0]

def get_yt_latest_video():
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "channelId": YOUTUBE_CHANNEL_ID,
        "order": "date",
        "maxResults": 1,
        "part": "snippet"
    }
    data = yt_request(url, params)
    if "items" not in data:
        return None
    return data["items"][0]

@app.route("/api/youtube")
def api_youtube():
    channel = get_yt_channel_stats()
    video = get_yt_latest_video()

    if not channel:
        return jsonify({"error": "No channel data"}), 500

    stats = channel["statistics"]
    snippet = channel["snippet"]

    info = {
        "subscribers": stats.get("subscriberCount", 0),
        "views_total": stats.get("viewCount", 0),
        "title": snippet.get("title", "-"),
        "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        "latest_video_title": video["snippet"]["title"] if video else "-",
        "latest_video_thumbnail": video["snippet"]["thumbnails"]["high"]["url"] if video else "",
    }

    return jsonify(info)

# =====================================================
# ===================== FRONTEND ======================
# =====================================================

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)
