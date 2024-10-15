import threading
import time
from fastapi import FastAPI
import uvicorn

class SyslogServer:
    def __init__(self):
        self.is_running = False
        self._stop_event = threading.Event()

    def start(self):
        if self.is_running:
            print("Syslog server is already running.")
            return
        self.is_running = True
        self._stop_event.clear()
        print("Syslog server started.")
        self._run()

    def _run(self):
        while not self._stop_event.is_set():
            # Symulacja działania serwera syslog
            time.sleep(1)
            print("Syslog server is running...")

    def stop(self):
        if not self.is_running:
            print("Syslog server is not running.")
            return
        self._stop_event.set()
        self.is_running = False
        print("Syslog server stopped.")

class Application:
    def __init__(self):
        self.syslog_server = SyslogServer()
        self.api_app = FastAPI()
        self._configure_api()

    def _configure_api(self):
        @self.api_app.get("/api/server/start")
        async def start_syslog():
            threading.Thread(target=self.syslog_server.start).start()
            return {"message": "Syslog server starting."}

        @self.api_app.get("/api/server/stop")
        async def stop_syslog():
            threading.Thread(target=self.syslog_server.stop).start()
            return {"message": "Syslog server stopping."}

    def start_syslog_server(self):
        threading.Thread(target=self.syslog_server.start).start()

    def start_api(self):
        # Uruchomienie serwera FastAPI w osobnym wątku
        config = uvicorn.Config(self.api_app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        threading.Thread(target=server.run, daemon=True).start()

    def run(self):
        # Uruchom API i serwer syslog w oddzielnych wątkach
        self.start_api()
        self.start_syslog_server()

if __name__ == "__main__":
    app = Application()
    app.run()
