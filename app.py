import os
from flask import Flask, request, jsonify, send_file
import google.generativeai as genai
import requests

app = Flask(__name__)

# A kulcsot szigorúan a Render titkos rendszeréből olvassuk ki!
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "HIÁNYZIK")
genai.configure(api_key=GEMINI_API_KEY)

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"ready": True if GEMINI_API_KEY != "HIÁNYZIK" else False})

@app.route('/process_audio', methods=['GET'])
def process_audio():
    try:
        # A kérdést egyszerűen a linkből olvassuk ki (?q=szia)
        gépelt_kérdés = request.args.get("q", "szia")
        print(f"Érkezett kérdés: {gépelt_kérdés}")

        if GEMINI_API_KEY == "HIÁNYZIK":
            valasz_szoveg = "Hiba: Az API kulcs nincs beallitva a Renderen!"
        else:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(f"Válaszolj erre a kérdésre magyarul, maximum egy rövid mondatban, ékezetek nélkül: {gépelt_kérdés}")
            valasz_szoveg = response.text
            
        print(f"Gemini válasza: {valasz_szoveg}")

        # Hang generálása
        tts_url = f"https://google.com{valasz_szoveg.replace(' ', '%20')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        audio_data = requests.get(tts_url, headers=headers).content
        
        with open("/tmp/output.mp3", "wb") as f:
            f.write(audio_data)

        render_url = request.url_root.rstrip('/')
        return jsonify({
            "message": valasz_szoveg,
            "stream_url": f"{render_url}/get_audio"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_audio', methods=['GET'])
def get_audio():
    return send_file("/tmp/output.mp3", mimetype="audio/mp3")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)
