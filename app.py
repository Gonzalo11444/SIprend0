import os
from flask import Flask, jsonify
from dotenv import load_dotenv
import requests
from token_manager import refresh_access_token

load_dotenv()

app = Flask(__name__)

CLIENT_ID = os.getenv("CLIENT_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def twitch_request(url, params=None):
    global ACCESS_TOKEN

    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    r = requests.get(url, headers=headers, params=params)

    # Si el token expiró → refrescamos automáticamente
    if r.status_code == 401:
        print("⚠️ Token expirado — refrescando...")
        ACCESS_TOKEN = refresh_access_token()

        headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"
        r = requests.get(url, headers=headers, params=params)

    return r.json()

@app.route("/api/status")
def status():
    # Información del usuario
    user_data = twitch_request(
        "https://api.twitch.tv/helix/users",
        {"id": USER_ID}
    )

    # Info de stream (si está en directo)
    stream_data = twitch_request(
        "https://api.twitch.tv/helix/streams",
        {"user_id": USER_ID}
    )

    stream_online = len(stream_data.get("data", [])) > 0
    if stream_online:
        stream = stream_data["data"][0]
        title = stream["title"]
        viewer_count = stream["viewer_count"]
    else:
        title = "-"
        viewer_count = 0

    user = user_data["data"][0]

    return jsonify({
        "display_name": user["display_name"],
        "login": user["login"],
        "user_id": user["id"],
        "views_total": user["view_count"],
        "followers": user["view_count"],   # OJO: esto no es followers reales, luego lo corregimos
        "stream_online": stream_online,
        "title": title,
        "viewer_count": viewer_count
    })

if __name__ == "__main__":
    app.run(debug=True)
