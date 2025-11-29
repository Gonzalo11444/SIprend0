from flask import Flask, jsonify, render_template
import requests, logging, os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# ----------------- CONFIG -----------------
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
USER_ID = os.getenv("USER_ID")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# ----------------- POSTGRESQL CONNECTION -----------------
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS twitch_stats (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        followers INT,
        viewers INT,
        stream_online BOOLEAN,
        total_views INT,
        title TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS youtube_stats (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP DEFAULT NOW(),
        subscribers INTEGER,
        views_total INTEGER,
        latest_video_title TEXT
    );
    """)
    conn.commit()
    cur.close()
    conn.close()
    logging.info("Base de datos inicializada")

init_db()

# ----------------- TWITCH FUNCTIONS -----------------
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
    logging.info("Token actualizado automáticamente")
    return True

def get_headers():
    return {"Client-ID": CLIENT_ID, "Authorization": f"Bearer {ACCESS_TOKEN}"}

def safe_request(url):
    r = requests.get(url, headers=get_headers())
    if r.status_code == 401:
        logging.info("Token expirado, refrescando...")
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

    save_twitch_stats(followers, info["viewer_count"], info["title"])
    return jsonify(info)

# ----------------- YOUTUBE FUNCTIONS -----------------
def yt_request(url, params):
    params["key"] = YOUTUBE_API_KEY
    r = requests.get(url, params=params)
    data = r.json()
    logging.info("Respuesta YouTube: %s", data)  # <-- log para depurar
    return data

def get_yt_channel_stats():
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {"id": YOUTUBE_CHANNEL_ID, "part": "statistics"}
    data = yt_request(url, params)
    if "items" not in data or not data["items"]:
        return None
    return data["items"][0]

def get_yt_latest_video():
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "channelId": YOUTUBE_CHANNEL_ID,
        "order": "date",
        "maxResults": 1,
        "part": "snippet",
        "type": "video"
    }
    data = yt_request(url, params)
    if "items" not in data or not data["items"]:
        return None
    return data["items"][0]

@app.route("/api/youtube")
def api_youtube():
    channel = get_yt_channel_stats()
    video = get_yt_latest_video()

    if not channel:
        logging.error("No se pudo obtener datos del canal de YouTube")
        return jsonify({"error": "No se pudo obtener datos del canal"}), 500

    stats = channel.get("statistics", {})

    latest_video_title = "-"
    latest_video_thumbnail = ""
    if video and "snippet" in video:
        latest_video_title = video["snippet"].get("title", "-")
        latest_video_thumbnail = video["snippet"].get("thumbnails", {}).get("high", {}).get("url", "")

    info = {
        "subscribers": stats.get("subscriberCount", 0),
        "views_total": stats.get("viewCount", 0),
        "latest_video_title": latest_video_title,
        "latest_video_thumbnail": latest_video_thumbnail,
    }

    save_youtube_stats(info["subscribers"], info["views_total"], info["latest_video_title"])
    return jsonify(info)

# ----------------- DB SAVE -----------------
def save_twitch_stats(followers, viewers, title):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT followers, viewers, title FROM twitch_stats ORDER BY timestamp DESC LIMIT 1")
    last = cur.fetchone()
    if last is None or (last[0] != followers or last[1] != viewers or last[2] != title):
        cur.execute(
            "INSERT INTO twitch_stats (followers, viewers, title) VALUES (%s, %s, %s)",
            (followers, viewers, title)
        )
        conn.commit()
    cur.close()
    conn.close()

def save_youtube_stats(subscribers, total_views, latest_video_title):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT subscribers, total_views, latest_video_title FROM youtube_stats ORDER BY timestamp DESC LIMIT 1")
    last = cur.fetchone()
    if last != (subscribers, total_views, latest_video_title):
        cur.execute(
            "INSERT INTO youtube_stats (subscribers, total_views, latest_video_title) VALUES (%s, %s, %s)",
            (subscribers, total_views, latest_video_title)
        )
        conn.commit()
    cur.close()
    conn.close()

# ----------------- FRONTEND -----------------
@app.route("/")
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)
