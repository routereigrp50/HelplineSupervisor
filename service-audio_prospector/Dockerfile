FROM python:3.11-slim

WORKDIR /app

COPY /handlers /app/handlers
COPY /audio_prospector.py /app/audio_prospector.py
COPY /run.py /app/run.py
COPY /requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt
CMD ["python","run.py"]
