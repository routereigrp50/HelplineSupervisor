from handlers.logging import Logging as h_log
from handlers.database import Database as h_db
import threading
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn



class JobSupervisor:
    def __init__(self):
        self._api = FastAPI(title="Job Supervisor", version="v0.2",openapi_tags=[{"name":"Job monitoring","description":"Operation related to job monitoring"},{"name":"Job operations","description":"Operation related to start / stop job operations"}])
        self._api_config = None
        self._api_hit_counter = 1
        self._api_routing()

    def _api_routing(self) -> None:
        @self._api.get("/api/job/info",tags=["Job monitoring"])
        async def get_job_info(job_name: str = None):
            log_api_endpoint = "/api/job/info" if job_name == None else f"/api/job/info/{job_name}"
            h_log.create_log(4, "job_supervisor.JobSupervisor._api_routing", f"S: API Call no. {self._api_hit_counter} - {log_api_endpoint}")
            '''
            Check if job_name is valid. Earlier there was no validation and then it just return 200 with empty array 
            but from my perspective is better to cut it there and dont allow to unnecesary db queries
            '''
            if job_name != None:
                valid_job_names = ["audioprospector"]
                if job_name not in valid_job_names:
                    h_log.create_log(2, "job_supervisor.JobSupervisor._api_routing", f"ENOK: API Call no. {self._api_hit_counter} - {log_api_endpoint} - Invalid job name")
                    self._api_hit_counter+=1
                    return JSONResponse(content={"status":"failed","reason":"Invalid job name"}, status_code=400)
                db_query_filter = {"job_name": job_name}
            else:
                db_query_filter = None
            '''Get job info from db'''
            db_query_status, db_query_content = h_db.get_collection('jobs',filter = db_query_filter)
            if not db_query_status:
                h_log.create_log(2, "job_supervisor.JobSupervisor._api_routing", f"ENOK: API Call no. {self._api_hit_counter} - {log_api_endpoint} - {str(db_query_content)}")
                self._api_hit_counter+=1
                return JSONResponse(content={"status":"failed","reason":str(db_query_content)}, status_code=500)
            h_log.create_log(4, "job_supervisor.JobSupervisor._api_routing", f"EOK: API Call no. {self._api_hit_counter} - {log_api_endpoint}")
            self._api_hit_counter+=1
            return JSONResponse(content={"status":"success","content":db_query_content}, status_code=200)

        @self._api.post("/api/job/start",tags=["Job operations"])
        async def start_job(job_name: str, job_config: dict):
            log_api_endpoint = f"/api/job/start?job_name={job_name}&job_config={job_config}"
            h_log.create_log(4, "job_supervisor.JobSupervisor._api_routing", f"S: API Call no. {self._api_hit_counter} - {log_api_endpoint}")
            ''' Check if job_name is valid '''
            valid_job_names = ["audioprospector"]
            if job_name not in valid_job_names:
                h_log.create_log(2, "job_supervisor.JobSupervisor._api_routing", f"ENOK: API Call no. {self._api_hit_counter} - {log_api_endpoint} - Invalid job name")
                self._api_hit_counter+=1
                return JSONResponse(content={"status":"failed","reason":"Invalid job name"}, status_code=400)
            ''' Run job '''
            job_run_status, job_run_content = self._job_run(job_name, job_config)
            if not job_run_status:
                h_log.create_log(2, "job_supervisor.JobSupervisor._api_routing", f"ENOK: API Call no. {self._api_hit_counter} - {log_api_endpoint} - {str(job_run_content)}")
                self._api_hit_counter+=1
                return JSONResponse(content={"status":"failed","reason":str(job_run_content)}, status_code=400)
            h_log.create_log(4, "job_supervisor.JobSupervisor._api_routing", f"EOK: API Call no. {self._api_hit_counter} - {log_api_endpoint}")
            self._api_hit_counter+=1
            return JSONResponse(content={"status":"success","content":job_run_content}, status_code=201)
        
        @self._api.post("api/job/stop/<job_name>",tags=["Job operations"])
        async def stop_job():
            return {"OK"}
        
    def api_set_config(self, configuration: dict) -> None:
        self._api_config = configuration
    
    def api_run(self) -> None:
        config = uvicorn.Config(self._api, host=self._api_config['ip'], port=self._api_config['port'], log_level="warning")
        server = uvicorn.Server(config)
        server.run()
    
    def _job_run(self, job_name: str, job_config: dict) -> tuple:
        match job_name:
            case "audioprospector":
                return (True, None)
            case _:
                return (False, "Invalid job name")