FROM python:3.11-slim

WORKDIR /app

COPY /handlers /app/handlers
COPY /conversation_peeper.py /app/conversation_peeper.py
COPY /run.py /app/run.py
COPY /requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt
CMD ["python","run.py"]

