import os
from flask import Flask, request, jsonify, send_file
import google.generativeai as genai
import requests

app = Flask(__name__)

# Gemini kulcs betöltése
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "HIÁNYZIK")
genai.configure(api_key=GEMINI_API_KEY)

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"ready": True if GEMINI_API_KEY != "HIÁNYZIK" else False})

@app.route('/process_audio', methods=['POST'])
def process_audio():
    try:
        # Beolvassuk a tiszta JSON kérdést az ESP32-től
        data = request.get_json(silent=True) or {}
        gépelt_kérdés = data.get("text", "szia")
        
        print(f"Érkezett gépelt kérdés: {gépelt_kérdés}")
        
        # Meghívjuk a Geminit tiszta szöveggel
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(f"Válaszolj erre a kérdésre magyarul, maximum egy nagyon rövid mondatban, ékezetek és speciális karakterek nélkül: {gépelt_kérdés}")
        
        valasz_szoveg = response.text
        print(f"Gemini válasza: {valasz_szoveg}")

        # Elkészítjük a tiszta MP3 hangot a Google Translate segítségével
        tts_url = f"https://google.com{valasz_szoveg.replace(' ', '%20')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        audio_data = requests.get(tts_url, headers=headers).content
        
        with open("/tmp/output.mp3", "wb") as f:
            f.write(audio_data)

        render_url = request.url_root.rstrip('/')
        
        # Visszaküldjük a pontos JSON válaszstruktúrát az ESP32-nek
        return jsonify({
            "message": valasz_szoveg,
            "file_id": "12345",
            "stream_url": f"{render_url}/get_audio"
        })

    except Exception as e:
        print(f"Hiba történt: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_audio', methods=['GET'])
def get_audio():
    return send_file("/tmp/output.mp3", mimetype="audio/mp3")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)
