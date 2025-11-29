from flask import Flask, request
import requests
import webbrowser
import time
import os
from dotenv import load_dotenv, set_key

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:5000/callback"
SCOPES = "user:read:email user:read:broadcast"

app = Flask(__name__)

@app.route("/callback")
def callback():
    code = request.args.get("code")

    # Intercambiar el code por tokens
    token_url = "https://id.twitch.tv/oauth2/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }

    r = requests.post(token_url, data=data)
    tokens = r.json()

    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    expires_in = tokens["expires_in"]

    # Guardar en .env
    set_key(".env", "ACCESS_TOKEN", access_token)
    set_key(".env", "REFRESH_TOKEN", refresh_token)

    return f"""
    <h1>Tokens generados correctamente</h1>
    <p>Access Token y Refresh Token guardados en .env</p>
    <p>Ya puedes cerrar esta ventana.</p>
    """

if __name__ == "__main__":
    # Abre el navegador automáticamente
    auth_url = (
        "https://id.twitch.tv/oauth2/authorize"
        f"?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES}"
    )

    print("Abriendo navegador para autorizar la app...")
    time.sleep(1)
    webbrowser.open(auth_url)

    # Inicia servidor local
    app.run(port=5000)
