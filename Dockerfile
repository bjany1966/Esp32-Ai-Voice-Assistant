# Ultrakönnyű, előre lefordított Python környezet használata
FROM python:3.9-slim

# Szükséges rendszerkomponensek (FFmpeg a hang feldolgozásához)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Munkakönyvtár beállítása
WORKDIR /code

# Csomaglista másolása és telepítése
COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /code/requirements.txt

# Teljes szoftverkód átmásolása
COPY . .

# Port megnyitása a Flask/FastAPI szervernek
EXPOSE 7860

# A szerver elindítása (Az app.py-ban lévő alkalmazást indítja)
CMD ["python", "app.py"]
