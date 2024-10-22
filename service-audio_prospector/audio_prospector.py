from handlers.logging import Logging as h_log
from handlers.database import Database as h_db
import threading
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn



class AudioProspector:
    def __inti__(self, api_configuration: dict) -> None:
        self._api = FastAPI(title="Audio Prospector", version="v0.2",openapi_tags=[]) #Create api object
        self._api_routing() #Set api routing
        self._api_run(api_configuration) #Run API
    
    def _api_run(self, api_configuration: dict) -> None:
        '''
        Create and run uvicorn server
        '''
        config = uvicorn.Config(self._api, host=api_configuration['ip'], port=api_configuration['port'], log_level="warning")
        server = uvicorn.Server(config)
        server.run()

    def _api_routing(self) -> None:
        '''
        Api routing configuration function. Core point of object logic
        '''
        @self._api.get("/")
        async def placeholder():
            return {"OK"}
