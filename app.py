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
        # Ha az Arduino szöveges tesztet küld a fejlécben
gépelt_kérdés = request.headers.get("X-Question", None)

if 'file' in request.files:
    audio_file = request.files['file']
    audio_file.save("/tmp/input.wav")
elif request.data and len(request.data) > 44:
    with open("/tmp/input.wav", "wb") as f:
        f.write(request.data)


        # 2. Beszédfelismerés és válasz a Geminivel egy lépésben!
        # Feltöltjük a hangfájlt közvetlenül a Google AI-ba
        uploaded_file = genai.upload_file(path="/tmp/input.wav")
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Megkérjük a Geminit, hogy hallgassa meg a hangot, és válaszoljon magyarul
        if gépelt_kérdés:
    response = model.generate_content(f"Válaszolj erre a kérdésre magyarul, maximum egy rövid mondatban, ékezetek nélkül: {gépelt_kérdés}")
else:
    uploaded_file = genai.upload_file(path="/tmp/input.wav")
    response = model.generate_content([uploaded_file, "Hallgasd meg ezt a magyar beszedhangot es valaszolj ra magyarul rovid egy mondatban ekezetek nelkul."])

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
