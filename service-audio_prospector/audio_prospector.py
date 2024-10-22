from handlers.logging import Logging as h_log
from handlers.database import Database as h_db
from tools.pydantic_models import AudioProspectorConfiguration
import threading
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn
import time


class AudioProspector:
    def __init__(self, api_configuration: dict) -> None:
        '''
        Api setters
        '''
        self._api = FastAPI(title="Audio Prospector", version="v0.2",openapi_tags=[{"name":"Monitoring"},{"name":"Operations"}]) 
        self._api_configuration = api_configuration
        self._api_hit_counter = 1
        '''
        Job setters
        '''
        self._job_thread = None
        self._job_configuration = {}
        '''
        Status update
        '''
        self.status = {"status":"OK","job":{"status":"Idle","configuration":self._job_configuration},"api":{"status":"OK","configuration":self._api_configuration}}
        '''
        Api run
        '''
        self._api_routing() #Set api routing
        self._api_run(self._api_configuration) #Run API


    def _api_run(self, api_configuration: dict) -> None:
        '''
        Create and run uvicorn server
        '''
        h_log.create_log(5, "audio_prospector._api_run", "Passing configuration to api object and running api server")
        try:
            config = uvicorn.Config(self._api, host=api_configuration['ip'], port=api_configuration['port'], log_level="warning")
            server = uvicorn.Server(config)
            server.run()
        except Exception as e:
            h_log.create_log(1, "audio_prospector._api_run", f"Failed to run api server. Reason {str(e)}")
            self.status['api']['status'] = "Failed"
            time.sleep(3), quit()

    def _api_routing(self) -> None:
        '''
        Api routing configuration function. Core point of object logic
        '''
        @self._api.get("/api/audioprospector/status",tags=['Monitoring'])
        async def get_job_status() -> JSONResponse:
            h_log.create_log(4, "audio_prospector._api_routing", f"S: API hit no. {self._api_hit_counter} get /api/audioprospector/status")
            h_log.create_log(4, "audio_prospector._api_routing", f"EOK: API hit no. {self._api_hit_counter} get /api/audioprospector/status")
            self._api_hit_counter+=1
            return JSONResponse(content=self.status,status_code=200)

        @self._api.post("/api/audioprospector/start",tags=['Operations'])
        async def start_job(raw_post_body: AudioProspectorConfiguration) -> JSONResponse:
            h_log.create_log(4, "audio_prospector._api_routing", f"S: API hit no. {self._api_hit_counter} post /api/audioprospector/start")
            post_body = raw_post_body.model_dump()
            return post_body

