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
        self._job_run_indicator = False
        self._job_configuration = {}
        '''
        Status update
        '''
        self.status = {"status":"OK","job":{"status":"IDLE","configuration":self._job_configuration},"api":{"status":"OK","configuration":self._api_configuration}}
        '''
        Api start
        '''
        self._api_routing() #Set api routing
        self._api_start(self._api_configuration) #start API


    def _api_start(self, api_configuration: dict) -> None:
        '''
        Create and start uvicorn server
        '''
        h_log.create_log(5, "audio_prospector._api_start", "Passing configuration to api object and startning api server")
        try:
            config = uvicorn.Config(self._api, host=api_configuration['ip'], port=api_configuration['port'], log_level="warning")
            server = uvicorn.Server(config)
            server.run()
        except Exception as e:
            h_log.create_log(1, "audio_prospector._api_start", f"Failed to start api server. Reason {str(e)}")
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
            return JSONResponse(content={"status":"OK","content":self.status},status_code=200)

        @self._api.post("/api/audioprospector/start",tags=['Operations'])
        async def start_job(post_body: AudioProspectorConfiguration) -> JSONResponse:
            h_log.create_log(4, "audio_prospector._api_routing", f"S: API hit no. {self._api_hit_counter} post /api/audioprospector/start")
            job_config = post_body.model_dump()
            start_status, start_error_msg = self._job_start(job_config)
            if not start_status:
                h_log.create_log(3, "audio_prospector._api_routing", f"ENOK: API hit no. {self._api_hit_counter} post /api/audioprospector/start")
                self._api_hit_counter+=1
                return JSONResponse(content={"status":"NOK","content":str(start_error_msg)},status_code=401)
            h_log.create_log(4, "audio_prospector._api_routing", f"EOK: API hit no. {self._api_hit_counter} post /api/audioprospector/start")
            self._api_hit_counter+=1
            return JSONResponse(content={"status":"OK", "content":""},status_code=201)
        
        @self._api.post("/api/audioprospector/stop",tags=['Operations'])
        async def stop_job() -> JSONResponse:
            h_log.create_log(4, "audio_prospector._api_routing", f"S: API hit no. {self._api_hit_counter} post /api/audioprospector/stop")
            stop_status, stop_error_msg = self._job_stop()
            if not stop_status:
                h_log.create_log(3, "audio_prospector._api_routing", f"ENOK: API hit no. {self._api_hit_counter} post /api/audioprospector/stop")
                self._api_hit_counter+=1
                return JSONResponse(content={"status":"NOK","content":str(stop_error_msg)},status_code=401)
            h_log.create_log(3, "audio_prospector._api_routing", f"EOK: API hit no. {self._api_hit_counter} post /api/audioprospector/stop")
            self._api_hit_counter+=1
            return JSONResponse(content={"status":"OK","content":""},status_code=201)
        
    def _job_start(self, job_configuration: dict) -> tuple:
        h_log.create_log(4, "audio_prospector._job_start", f"Attempting to start job with configuration: {job_configuration}")
        h_log.create_log(5, "audio_prospector._job_start", f"Attempting to verify current job status")
        if self.status['job']['status'] == "RUNNING":
            h_log.create_log(2, "audio_prospector._job_start", f"Current job status is 'RUNNING'")
            h_log.create_log(2, "audio_prospector._job_start", f"Failed to start job. Reason: Job is already RUNNING")
            return (False, "Job is already RUNNING")
        h_log.create_log(5, "audio_prospector._job_start", f"Current job status is {self.status['job']['status']}")
        h_log.create_log(5, "audio_prospector._job_start", f"Creating job thread")
        thread = threading.Thread(target = self.__job_loop, args = ())

        #ADD UPDATE IN SELF STATUS HERE TO WORKING

        h_log.create_log(5, "audio_prospector._job_start", f"Starting job thread")
        thread.start()
        h_log.create_log(4, "audio_prospector._job_start", f"Successfully started job with configuration: {job_configuration}")
        return (True, None)

    def _job_stop(self) -> tuple:
        h_log.create_log(4, "audio_prospector._job_stop", f"Attempting to stop job")
        h_log.create_log(5, "audio_prospector._job_stop", f"Attempting to verify current job status")
        if self.status['job']['status'] != "RUNNING":
            h_log.create_log(3, "audio_prospector._job_stop", f"Curren job statis is not 'RUNNING'")
            h_log.create_log(3, "audio_prospector._job_stop", f"Failed to stop job. Reason: Job is not RUNNING")
            return (False, "Job is not RUNNING")
        h_log.create_log(5, "audio_prospector._job_stop", f"Current job status is {self.status['job']['status']}")
        h_log.create_log(5, "audio_prospector._job_stop", f"Setting job flag indicator to False")
        self._job_run_indicator = False
        h_log.create_log(4, "audio_prospector._job_stop", f"Successfully stoped job")
        return (True, None)

    def __job_loop(self) -> None:
        while self._job_run_indicator:
            print(":)")
            time.sleep(5)

