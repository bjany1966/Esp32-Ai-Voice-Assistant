import os
from flask import Flask, request, jsonify, send_file
import google.generativeai as genai
import requests

app = Flask(__name__)

# Konfiguráljuk a Geminit a Renderen megadott környezeti változóból
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "HIÁNYZIK")
genai.configure(api_key=GEMINI_API_KEY)

@app.route('/status', methods=['GET'])
def status():
    # Az ESP32 setup() függvénye ezt hívja meg ellenőrzésként
    return jsonify({"ready": True if GEMINI_API_KEY != "HIÁNYZIK" else False})

@app.route('/process_audio', methods=['POST'])
def process_audio():
    try:
        # 1. Fogadjuk a hangfájlt az ESP32 mikrofonjáról
        if 'file' in request.files:
            audio_file = request.files['file']
            audio_file.save("/tmp/input.wav")
        else:
            # Ha nyers adatként küldi a mikrofon bájtokat
            with open("/tmp/input.wav", "wb") as f:
                f.write(request.data)

        # 2. Beszédfelismerés és válasz a Geminivel egy lépésben!
        # Feltöltjük a hangfájlt közvetlenül a Google AI-ba
        uploaded_file = genai.upload_file(path="/tmp/input.wav")
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Megkérjük a Geminit, hogy hallgassa meg a hangot, és válaszoljon magyarul
        response = model.generate_content([
            uploaded_file, 
            "Hallgasd meg ezt a magyar beszédhangot, értsd meg a kérdést, és válaszolj rá magyarul, maximum egy-két rövid mondatban, ékezetek nélkül."
        ])
        valasz_szoveg = response.text
        print(f"Gemini válasza: {valasz_szoveg}")

        # 3. Google Translate TTS (Létrehozzuk az MP3 hangfájlt a válaszból)
        tts_url = f"https://google.com{valasz_szoveg.replace(' ', '%20')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        audio_data = requests.get(tts_url, headers=headers).content
        
        with open("/tmp/output.mp3", "wb") as f:
            f.write(audio_data)

        # A Render külső címe (ezt automatikusan megkapja a szerver)
        render_url = request.url_root.rstrip('/')

        # Visszaküldjük a válaszokat pontosan úgy, ahogy az ESP32 kódja várja!
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
    # Ezen a linken keresztül fogja letölteni az ESP32 az MP3 hangfájlt
    return send_file("/tmp/output.mp3", mimetype="audio/mp3")

if __name__ == '__main__':
    # A Rendernek kötelező a 0.0.0.0 hoszt és a megadott PORT port!
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)
