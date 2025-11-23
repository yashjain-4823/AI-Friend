from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import requests

app = Flask(__name__, static_folder="static")
CORS(app)

API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-2.0-flash"
GEMINI_URL = None
if API_KEY:
    GEMINI_URL = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
    )

# ------ FRONTEND ROUTE ------
@app.route("/", methods=["GET"])
def serve_frontend():
    # static/chat.html serve karega
    return app.send_static_file("chat.html")


# ------ CHAT API ------
@app.route("/chat", methods=["POST"])
def chat():
    print("---- /chat hit ----")
    print("Content-Type:", request.content_type)

    if request.content_type and request.content_type.startswith("multipart/form-data"):
        user_message = (request.form.get("user_message") or "").strip()
        user_name = (request.form.get("user_name") or "").strip()
        history_raw = request.form.get("history") or "[]"
        try:
            history = json.loads(history_raw)
        except Exception:
            history = []
    else:
        data = request.get_json(silent=True) or {}
        user_message = (data.get("user_message") or "").strip()
        user_name = (data.get("user_name") or "").strip()
        history = data.get("history") or []

    print("user_message:", repr(user_message))

    if not user_message:
        return jsonify({"response_text": "Please type something 🙂"})

    # Agar API key nahi hai to simple local reply
    if not GEMINI_URL:
        reply = f"Hi! (local reply) You said: {user_message}"
        return jsonify({"response_text": reply})

    contents = [{"role": "user", "parts": [{"text": user_message}]}]
    payload = {"contents": contents}

    try:
        resp = requests.post(GEMINI_URL, json=payload, timeout=20)
        res_json = resp.json()
        print("Gemini status:", resp.status_code)

        if "candidates" not in res_json:
            print("Gemini raw response (no candidates):", res_json)
            error_msg = res_json.get("error", {}).get("message", "Unknown error from Gemini")
            raise RuntimeError(error_msg)

        bot_reply = res_json["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        print("Gemini Error:", repr(e))
        bot_reply = (
            "Something went wrong while talking to the AI 😅\n"
            "It might be a network, API key, or model issue. Please try again after some time."
        )

    return jsonify({"response_text": bot_reply})


if __name__ == "__main__":
    app.run(debug=True)
