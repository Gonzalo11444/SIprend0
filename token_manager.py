import os
import requests
from dotenv import load_dotenv, set_key

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")

def refresh_access_token():
    url = "https://id.twitch.tv/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    response = requests.post(url, data=data)
    data = response.json()

    if "access_token" in data:
        new_access = data["access_token"]
        new_refresh = data["refresh_token"]

        # Guardar en .env
        set_key(".env", "ACCESS_TOKEN", new_access)
        set_key(".env", "REFRESH_TOKEN", new_refresh)

        print("🔄 Token actualizado automáticamente.")
        return new_access

    print("❌ Error refrescando token:", data)
    return None
