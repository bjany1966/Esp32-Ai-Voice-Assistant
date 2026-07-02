# Előre lefordított, tiszta Python környezet
FROM python:3.9-slim

# Rendszerkomponensek telepítése (FFmpeg a hangkezeléshez)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Munkakönyvtár létrehozása
WORKDIR /code

# Kötelező frissítések és a csomaglista másolása
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
COPY requirements.txt /code/requirements.txt

# EZ HIÁNYZOTT: Itt telepítjük fel ténylegesen a Flask-ot és a többi modult!
RUN pip install --no-cache-dir -r /code/requirements.txt

# A teljes szoftverkód átmásolása
COPY . .

# Port beállítása
EXPOSE 7860

# Indítási parancs
CMD ["python", "app.py"]
