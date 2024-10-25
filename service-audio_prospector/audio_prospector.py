from handlers.logging import Logging as h_log
from handlers.database import Database as h_db
from tools.pydantic_models import AudioProspectorConfiguration
from tools.decorators import retry
import threading
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn
import time
from datetime import datetime, timezone
import os



class AudioProspector:
    def __init__(self, api_configuration: dict) -> None:
        '''
        API VARS
        '''
        self._api = FastAPI(title="Audio Prospector", version="v0.2",openapi_tags=[{"name":"Monitoring"},{"name":"Operations"}]) 
        self._api_configuration = api_configuration
        self._api_hit_counter = 1
        '''
        JOB VARS
        '''
        self._job_run_indicator = False
        self._job_configuration = {}
        self._job_loop_counter = 1
        self._job_error_counter = 1
        '''
        CLASS STATUS - THIS VALUE VILL BE QUESTIONED IN TASKS
        '''
        self.status = {"status":"OK","job":{"status":"IDLE","configuration":self._job_configuration},"api":{"status":"OK","configuration":self._api_configuration}}
        '''
        SECTION: RUN API
        '''
        self._api_routing()
        self._api_start(self._api_configuration)


    def _api_start(self, api_configuration: dict) -> None:
        '''
        FUNCTION: CREATE API OBJECT AND START UVICORN SERVER
        '''
        h_log.create_log(5, "audio_prospector._api_start", "Passing configuration to api object and startning api server")
        try:
            config = uvicorn.Config(self._api, host=api_configuration['ip'], port=api_configuration['port'], log_level="warning")
            server = uvicorn.Server(config)
            server.run()
        except Exception as e:
            h_log.create_log(1, "audio_prospector._api_start", f"Failed to start api server. Reason {str(e)}")
            self.status['api']['status'] = "FAILED"
            time.sleep(3), quit()

    def _api_routing(self) -> None:
        '''
        FUNCTION: API ROUTING
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
                return JSONResponse(content={"status":"NOK","content":str(start_error_msg)},status_code=400)
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
                return JSONResponse(content={"status":"NOK","content":str(stop_error_msg)},status_code=400)
            h_log.create_log(4, "audio_prospector._api_routing", f"EOK: API hit no. {self._api_hit_counter} post /api/audioprospector/stop")
            self._api_hit_counter+=1
            return JSONResponse(content={"status":"OK","content":""},status_code=201)
        
    def _job_start(self, job_configuration: dict) -> tuple:
        '''
        FUNCTION: RUN JOB INTERFACE
        '''
        h_log.create_log(4, "audio_prospector._job_start", f"Attempting to start job with configuration: {job_configuration}")
        h_log.create_log(5, "audio_prospector._job_start", f"Attempting to verify current job status")
        if self.status['job']['status'] == "RUNNING":
            h_log.create_log(2, "audio_prospector._job_start", f"Current job status is 'RUNNING'")
            h_log.create_log(2, "audio_prospector._job_start", f"Failed to start job. Reason: Job is already RUNNING")
            return (False, "Job is already RUNNING")
        h_log.create_log(5, "audio_prospector._job_start", f"Current job status is {self.status['job']['status']}")
        h_log.create_log(5, "audio_prospector._job_start", f"Creating job thread")
        thread = threading.Thread(target = self.__job_loop, args = ())
        h_log.create_log(5, "audio_prospector._job_start", f"Starting job thread")
        self._job_run_indicator = True
        thread.start()
        self.status['job']['status'] = "RUNNING"
        self.status['job']['configuration'] = job_configuration
        self._job_configuration = job_configuration
        h_log.create_log(4, "audio_prospector._job_start", f"Successfully started job with configuration: {job_configuration}")
        return (True, None)

    def _job_stop(self) -> tuple:
        '''
        FUNCTION: STOP JOB INTERFACE
        '''
        h_log.create_log(4, "audio_prospector._job_stop", f"Attempting to stop job")
        h_log.create_log(5, "audio_prospector._job_stop", f"Attempting to verify current job status")
        if self.status['job']['status'] != "RUNNING":
            h_log.create_log(3, "audio_prospector._job_stop", f"Curren job statis is not 'RUNNING'")
            h_log.create_log(3, "audio_prospector._job_stop", f"Failed to stop job. Reason: Job is not RUNNING")
            return (False, "Job is not RUNNING")
        h_log.create_log(5, "audio_prospector._job_stop", f"Current job status is {self.status['job']['status']}")
        h_log.create_log(5, "audio_prospector._job_stop", f"Setting job flag indicator to False")
        self._job_run_indicator = False
        self._job_loop_counter = 1
        self._job_error_counter = 1
        self.status['job']['status'] = "IDLE"
        self.status['job']['configuration'] = {}
        h_log.create_log(4, "audio_prospector._job_stop", f"Successfully stoped job")
        return (True, None)

    def __job_loop(self) -> None:
        '''
        FUNCTION: CORE JOB FUNCTION
        '''
        while self._job_run_indicator:
            h_log.create_log(4, "audio_prospector.__job_loop", f"Starting loop iteration no. {self._job_loop_counter}")
            '''
            SECTION: SCAN FOR FILES
            '''
            h_log.create_log(5, "audio_prospector.__job_loop", f"Attempting to scan for audio files")
            try:
                list_of_files = []
                if os.path.exists(self._job_configuration['path']):
                    for root, dirs, files in os.walk(self._job_configuration['path']):
                        for file in files:
                            if file.endswith(self._job_configuration['audio_extension']):
                                raw_path = os.path.join(root, file)
                                norm_path = os.path.normpath(raw_path)
                                formated_path = norm_path.replace("\\","/")
                                list_of_files.append(formated_path)
                else:
                    h_log.create_log(2, "audio_prospector.__job_loop", f"Failed to scan for audio files. Reason: Configured audio path {self._job_configuration['path']} does not exist")
                    h_log.create_log(4, "audio_prospector.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: NOK. Sleeptime before next iteration: {self._job_error_counter*self._job_configuration['scanning_interval']}. Time extended due to NOK")
                    time.sleep(self._job_error_counter*10)
                    self._job_loop_counter+=1
                    self._job_error_counter+=1
                    continue
            except Exception as e:
                h_log.create_log(2, "audio_prospector.__job_loop", f"Failed to scan for audio files. Reason:{str(e)}")
                h_log.create_log(4, "audio_prospector.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: NOK. Sleeptime before next iteration: {self._job_error_counter*self._job_configuration['scanning_interval']}. Time extended due to NOK")
                time.sleep(self._job_error_counter*10)
                self._job_loop_counter+=1
                self._job_error_counter+=1
                continue
            h_log.create_log(5, "audio_prospector.__job_loop", f"Successfully scanned for audio files. {str(len(list_of_files))} files found")
            '''
            SECTION: GET LAST SCAN FROM DB
            '''
            h_log.create_log(5, "audio_prospector.__job_loop", f"Attempting to get last scan from database")
            db_result, db_content = h_db.get_collection("ap_last_scan")
            if not db_result:
                h_log.create_log(2, "audio_prospector.__job_loop", f"Failed to get last scan from database")
                h_log.create_log(4, "audio_prospector.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: NOK. Sleeptime before next iteration: {self._job_error_counter*self._job_configuration['scanning_interval']}. Time extended due to NOK")
                time.sleep(self._job_error_counter*10)
                self._job_loop_counter+=1
                self._job_error_counter+=1
                continue
            h_log.create_log(5, "audio_prospector.__job_loop", f"Successfully got last scan from database")
            '''
            SECTION: CORE JOB LOGIC
            - CHECK IF ANY LAST SCAN EXIST IN DATABASE
                - IF EXIST CALCULATE DIFFERENCE
                    - IF NO DIFFERENCE SLEEP AND RETRY LOOP
                    - IF DIFFERENCE SAVE DIFFERENCE TO DB QUEUE AND CURRENT SCAN AS LAST SCAN IN DB
                - IF LAST SCAN DONT EXIST SAVE CURRENT SCAN TO DB QUEUE AND AS LAST SCAN IN DB
            '''
            if len(db_content) > 0: #IF LAST SCAN EXIST
                h_log.create_log(5, "audio_prospector.__job_loop", f"{len(db_content)} files found in last scan database collection")
                h_log.create_log(5, "audio_prospector.__job_loop", f"Attempting to calculate difference between local and last scan")
                decaps_last_scan = [x['path'] for x in db_content]
                difference = list(set(list_of_files) - set(decaps_last_scan))
                if len(difference) == 0: #IF THERE IS NO DIFFERENCE BETWEEN LAST SCAN AND CURRENT SCAN
                    h_log.create_log(5, "audio_prospector.__job_loop", f"Successfully calculated difference between local and last scan. Result: No difference")
                    h_log.create_log(4, "audio_prospector.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: OK. Sleeptime before next iteration: {self._job_configuration['scanning_interval']}.")
                    time.sleep(self._job_configuration['scanning_interval'])
                    self._job_loop_counter+=1
                    continue
                #IF THERE IS DIFFERENCE
                h_log.create_log(5, "audio_prospector.__job_loop", f"Successfully calculated difference between local and last scan. Result: {len(difference)} new files")
                h_log.create_log(5, "audio_prospector.__job_loop", f"Attempting to fill database collections")
                q_save_result, q_save_content = self.__save_files_in_db("ap_queue",difference)
                ls_save_result, ls_save_content = self.__save_files_in_db("ap_last_scan",difference)
                if not q_save_result or not ls_save_result:
                    h_log.create_log(2, "audio_prospector.__job_loop", f"Failed to fill database collection")
                    h_log.create_log(4, "audio_prospector.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: NOK. Sleeptime before next iteration: {self._job_error_counter*self._job_configuration['scanning_interval']}. Time extended due to NOK")
                    time.sleep(self._job_error_counter*10)
                    self._job_loop_counter+=1
                    self._job_error_counter+=1
                    continue
                h_log.create_log(5, "audio_prospector.__job_loop", f"Successfully filled database collections")
                h_log.create_log(4, "audio_prospector.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: OK. Sleeptime before next iteration: {self._job_configuration['scanning_interval']}.")
                time.sleep(self._job_configuration['scanning_interval'])
                self._job_loop_counter+=1
                continue
            else: #IF LAST SCAN DONT EXIST
                h_log.create_log(5, "audio_prospector.__job_loop", f"No files found in last scan dabatase collection")
                h_log.create_log(5, "audio_prospector.__job_loop", f"Attempting to save current scan to queue and last scan database collections")
                q_save_result, q_save_content = self.__save_files_in_db("ap_queue", list_of_files)
                ls_save_result, ls_save_content = self.__save_files_in_db("ap_last_scan", list_of_files)
                if not q_save_result or not ls_save_result:
                    h_log.create_log(2, "audio_prospector.__job_loop", f"Failed to fill database collection")
                    h_log.create_log(4, "audio_prospector.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: NOK. Sleeptime before next iteration: {self._job_error_counter*self._job_configuration['scanning_interval']}. Time extended due to NOK")
                    time.sleep(self._job_error_counter*10)
                    self._job_loop_counter+=1
                    self._job_error_counter+=1
                    continue
                h_log.create_log(5, "audio_prospector.__job_loop",f"Successfully filled database collections")
                h_log.create_log(4, "audio_prospector.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: OK. Sleeptime before next iteration: {self._job_configuration['scanning_interval']}.")
                time.sleep(self._job_configuration['scanning_interval'])
                self._job_loop_counter+=1
                continue    
        
    def __save_files_in_db(self, db_collection_name: str, list_of_files: list) -> tuple:
        '''
        FUNCTION: CORE JOB LOOP SUPPORTING FUNCTION. FILL DATABASE COLLECTION WITH PATH OF FILES
        '''
        current_timestamp = datetime.now(timezone.utc)
        formated_list_of_files = []
        for item in list_of_files:
            formated_list_of_files.append({"path":item,"timestamp":current_timestamp})
        insert_result, insert_content = h_db.insert_many(db_collection_name,formated_list_of_files)
        return (insert_result, insert_content)
