from handlers.logging import Logging as h_log
from handlers.database import Database as h_db
import threading
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn



class AudioProspector:
    def __init__(self) -> tuple:
        self._api = FastAPI(title="Job - Audio Prospector", version="v0.2",openapi_tags=[])
        self._api_config = None
        self._api_hit_counter = 1
        self._api_routing()
        #Jakis job status frame by sie przydał
        #Call funkcji do aktualizacji stanu joba w db

    def _api_routing(self) -> None:
        pass

    def api_set_config(self, configuration: dict) -> None:
        self._api_config = configuration
    
    def api_run(self) -> None:
        #Dodaj sprawdzanie czy api_config na pewno nie jest dalej None!
        config = uvicorn.Config(self._api, host=self._api_config['ip'], port=self._api_config['port'], log_level="warning")
        server = uvicorn.Server(config)
        #Dodaj aktualizacje statusu joba w DB
        server.run()

    def _job_raport_status(self, job_status: str, job_config: dict) -> tuple:
        pass

    def _job_start(self, job_config: dict) -> tuple:
        pass
    
    def _job_stop(self, job_name: str) -> tuple:
        pass
    
    def _job_loop(self) -> None:
        pass