import os
from flask import Flask, request, jsonify, send_file
import google.generativeai as genai
import requests

app = Flask(__name__)

# Konfiguráljuk a Geminit
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "HIÁNYZIK")
genai.configure(api_key=GEMINI_API_KEY)

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"ready": True if GEMINI_API_KEY != "HIÁNYZIK" else False})

@app.route('/process_audio', methods=['POST'])
def process_audio():
    try:
        # Kiolvassuk az Arduino által küldött gépelt kérdést a fejlécből
        gépelt_kérdés = request.headers.get("X-Question", None)
        
        # Audio fájl kezelése (ha mikrofonról érkezik)
        if 'file' in request.files:
            audio_file = request.files['file']
            audio_file.save("/tmp/input.wav")
        elif request.data and len(request.data) > 44:
            with open("/tmp/input.wav", "wb") as f:
                f.write(request.data)

        # Gemini meghívása a kérés típusától függően
        if gépelt_kérdés:
            print(f"Gépelt kérdés érkezett: {gépelt_kérdés}")
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(f"Válaszolj erre a kérdésre magyarul, maximum egy rövid mondatban, ékezetek nélkül: {gépelt_kérdés}")
        else:
            uploaded_file = genai.upload_file(path="/tmp/input.wav")
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content([
                uploaded_file, 
                "Hallgasd meg ezt a magyar beszedhangot es valaszolj ra magyarul rovid egy mondatban ekezetek nelkul."
            ])
            
        valasz_szoveg = response.text
        print(f"Gemini válasza: {valasz_szoveg}")

        # Hang generálása MP3-ba a Google Translate segítségével
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
