FROM python:3.11-slim

WORKDIR /app

COPY /handlers /app/handlers
COPY /tools /app/tools
COPY /run.py /app/run.py
COPY /config.json /app/config.json
COPY /requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "run.py"]