import os
from flask import Flask, request, jsonify, send_file
import google.generativeai as genai
import requests

app = Flask(__name__)

# Gemini kulcs betöltése a Renderből
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "HIÁNYZIK")
genai.configure(api_key=GEMINI_API_KEY)

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"ready": True if GEMINI_API_KEY != "HIÁNYZIK" else False})

@app.route('/process_audio', methods=['POST'])
def process_audio():
    try:
        gépelt_kérdés = None
        
        # 1. MEGOLDÁS: Megpróbáljuk beolvasni JSON szövegként
        if request.is_json:
            data = request.get_json(silent=True) or {}
            gépelt_kérdés = data.get("text", None)
        
        # 2. MEGOLDÁS: Megnézzük, hogy az egyedi X-Question fejlécben küldte-e az ESP
        if not gépelt_kérdés:
            gépelt_kérdés = request.headers.get("X-Question", None)

        print(f"Feldolgozás indítása... Kérdés szövege: {gépelt_kérdés}")

        # Gemini meghívása a tiszta szöveggel
        if gépelt_kérdés:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(f"Válaszolj erre a kérdésre magyarul, maximum egy nagyon rövid mondatban, ékezetek és speciális karakterek nélkül: {gépelt_kérdés}")
            valasz_szoveg = response.text
        else:
            # Biztonsági háló, ha minden adat üresen jönne be, akkor se legyen 400-as hiba!
            valasz_szoveg = "Szia! A kapcsolat teljesen sikeres, keszen allok a feladatra!"
            
        print(f"Gemini válasza: {valasz_szoveg}")

        # Hang generálása MP3 formátumban a Google Translate segítségével
        tts_url = f"https://google.com{valasz_szoveg.replace(' ', '%20')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        audio_data = requests.get(tts_url, headers=headers).content
        
        with open("/tmp/output.mp3", "wb") as f:
            f.write(audio_data)

        render_url = request.url_root.rstrip('/')
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
