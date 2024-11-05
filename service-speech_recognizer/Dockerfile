FROM python:3.11-slim

WORKDIR /app

COPY /handlers /app/handlers
COPY /speech_recognizer.py /app/speech_recognizer.py
COPY /run.py /app/run.py
COPY /requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt
CMD ["python","run.py"]

