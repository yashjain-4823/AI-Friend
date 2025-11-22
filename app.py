from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-2.0-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("user_message", "").strip()
    history = data.get("history", [])  # [{role:'user'/'model', text:'...'}]
    user_name = data.get("user_name", "").strip()

    if not user_message:
        return jsonify({"response_text": "Please type something 🙂"})

    # Build contents list for Gemini from history
    contents = []

    # If we know the user's name, insert a small "system-style" instruction
    if user_name:
        contents.append({
            "role": "user",
            "parts": [{
                "text": f"My name is {user_name}. Please call me {user_name} sometimes and be a friendly study buddy."
            }]
        })

    for msg in history:
        role = msg.get("role", "user")
        text = msg.get("text", "")
        if not text:
            continue
        # Gemini roles: "user" or "model"
        if role not in ("user", "model"):
            role = "user"
        contents.append({
            "role": role,
            "parts": [{"text": text}]
        })

    # Latest user message
    contents.append({
        "role": "user",
        "parts": [{"text": user_message}]
    })

    payload = {"contents": contents}

    try:
        resp = requests.post(GEMINI_URL, json=payload)
        res_json = resp.json()

        if "candidates" not in res_json:
            print("Gemini raw response (no candidates):", res_json)
            error_msg = res_json.get("error", {}).get("message", "Unknown error from Gemini")
            raise RuntimeError(error_msg)

        bot_reply = res_json["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        print("Gemini Error:", repr(e))
        bot_reply = (
            "Bhai AI side pe kuch error aa gaya 😅\n"
            "Ho sakta hai API key / model ya network ka issue ho. Thodi der baad try kar lena."
        )

    return jsonify({"response_text": bot_reply})


if __name__ == "__main__":
    app.run(debug=True)
