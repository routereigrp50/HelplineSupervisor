from handlers.logging import Logging as h_log
from handlers.database import Database as h_db
from handlers.azure import Azure
from tools.pydantic_models import SpeechRecognizerConfiguration
from tools.decorators import retry
import threading
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn
import time
from datetime import datetime, timezone
import os
from bson import ObjectId




class SpeechRecognizer:
    def __init__(self, api_configuration: dict) -> None:
        '''
        API VARS
        '''
        self._api = FastAPI(title="Speech Recognizer", version="v0.2",openapi_tags=[{"name":"Monitoring"},{"name":"Operations"}]) 
        self._api_configuration = api_configuration
        self._api_hit_counter = 1
        '''
        JOB VARS
        '''
        self._job_run_indicator = False
        self._job_configuration = {}
        self._job_loop_counter = 1
        self._job_error_counter = 1
        self._job_chached_queue = []
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
        h_log.create_log(5, "speech_recognizer._api_start", "Passing configuration to api object and startning api server")
        try:
            config = uvicorn.Config(self._api, host=api_configuration['ip'], port=api_configuration['port'], log_level="warning")
            server = uvicorn.Server(config)
            server.run()
        except Exception as e:
            h_log.create_log(1, "speech_recognizer._api_start", f"Failed to start api server. Reason {str(e)}")
            self.status['api']['status'] = "FAILED"
            time.sleep(3), quit()
    
    def _api_routing(self) -> None:
        '''
        FUNCTION: API ROUTING
        '''
        @self._api.get("/api/speechrecognizer/status",tags=['Monitoring'])
        async def get_job_status() -> JSONResponse:
            h_log.create_log(4, "speech_recognizer._api_routing", f"S: API hit no. {self._api_hit_counter} get /api/speechrecognizer/status")
            h_log.create_log(4, "speech_recognizer._api_routing", f"EOK: API hit no. {self._api_hit_counter} get /api/speechrecognizer/status")
            self._api_hit_counter+=1
            return JSONResponse(content={"status":"OK","content":self.status},status_code=200)

        @self._api.post("/api/speechrecognizer/start",tags=['Operations'])
        async def start_job(post_body: SpeechRecognizerConfiguration) -> JSONResponse:
            h_log.create_log(4, "speech_recognizer._api_routing", f"S: API hit no. {self._api_hit_counter} post /api/speechrecognizer/start")
            job_config = post_body.model_dump()
            start_status, start_error_msg = self._job_start(job_config)
            if not start_status:
                h_log.create_log(3, "speech_recognizer._api_routing", f"ENOK: API hit no. {self._api_hit_counter} post /api/speechrecognizer/start")
                self._api_hit_counter+=1
                return JSONResponse(content={"status":"NOK","content":str(start_error_msg)},status_code=400)
            h_log.create_log(4, "speech_recognizer._api_routing", f"EOK: API hit no. {self._api_hit_counter} post /api/speechrecognizer/start")
            self._api_hit_counter+=1
            return JSONResponse(content={"status":"OK", "content":""},status_code=201)
        
        @self._api.post("/api/speechrecognizer/stop",tags=['Operations'])
        async def stop_job() -> JSONResponse:
            h_log.create_log(4, "speech_recognizer._api_routing", f"S: API hit no. {self._api_hit_counter} post /api/speechrecognizer/stop")
            stop_status, stop_error_msg = self._job_stop()
            if not stop_status:
                h_log.create_log(3, "speech_recognizer._api_routing", f"ENOK: API hit no. {self._api_hit_counter} post /api/speechrecognizer/stop")
                self._api_hit_counter+=1
                return JSONResponse(content={"status":"NOK","content":str(stop_error_msg)},status_code=400)
            h_log.create_log(4, "speech_recognizer._api_routing", f"EOK: API hit no. {self._api_hit_counter} post /api/speechrecognizer/stop")
            self._api_hit_counter+=1
            return JSONResponse(content={"status":"OK","content":""},status_code=201)

    def _job_start(self, job_configuration: dict) -> tuple:
        '''
        FUNCTION: RUN JOB INTERFACE
        '''
        h_log.create_log(4, "speech_recognizer._job_start", f"Attempting to start job with configuration: {job_configuration}")
        h_log.create_log(5, "speech_recognizer._job_start", f"Attempting to verify current job status")
        if self.status['job']['status'] == "RUNNING":
            h_log.create_log(2, "speech_recognizer._job_start", f"Current job status is 'RUNNING'")
            h_log.create_log(2, "speech_recognizer._job_start", f"Failed to start job. Reason: Job is already RUNNING")
            return (False, "Job is already RUNNING")
        h_log.create_log(5, "speech_recognizer._job_start", f"Current job status is {self.status['job']['status']}")
        h_log.create_log(5, "speech_recognizer._job_start", f"Creating job thread")
        thread = threading.Thread(target = self.__job_loop, args = ())
        h_log.create_log(5, "speech_recognizer._job_start", f"Starting job thread")
        self._job_run_indicator = True
        thread.start()
        self.status['job']['status'] = "RUNNING"
        self.status['job']['configuration'] = job_configuration
        self._job_configuration = job_configuration
        h_log.create_log(4, "speech_recognizer._job_start", f"Successfully started job with configuration: {job_configuration}")
        return (True, None)

    def _job_stop(self) -> tuple:
        '''
        FUNCTION: STOP JOB INTERFACE
        '''
        h_log.create_log(4, "speech_recognizer._job_stop", f"Attempting to stop job")
        h_log.create_log(5, "speech_recognizer._job_stop", f"Attempting to verify current job status")
        if self.status['job']['status'] != "RUNNING":
            h_log.create_log(3, "speech_recognizer._job_stop", f"Current job statis is not 'RUNNING'")
            h_log.create_log(3, "speech_recognizer._job_stop", f"Failed to stop job. Reason: Job is not RUNNING")
            return (False, "Job is not RUNNING")
        h_log.create_log(5, "speech_recognizer._job_stop", f"Current job status is {self.status['job']['status']}")
        h_log.create_log(5, "speech_recognizer._job_stop", f"Setting job flag indicator to False")
        self._job_run_indicator = False
        self._job_loop_counter = 1
        self._job_error_counter = 1
        self.status['job']['status'] = "IDLE"
        self.status['job']['configuration'] = {}
        h_log.create_log(4, "speech_recognizer._job_stop", f"Successfully stoped job")
        return (True, None)

    def __job_loop(self) -> None:
        '''
        FUNCTION: CORE JOB FUNCTION
        '''
        while self._job_run_indicator:
            h_log.create_log(4, "speech_recognizer.__job_loop", f'Starting loop iteration no. {self._job_loop_counter}')
            '''
            SECTION: GET FILE FROM Q
            '''
            if not self._job_chached_queue: #IF THERE ARE NO CACHED ENTRIES
                h_log.create_log(5, "speech_recognizer.__job_loop", f"No cached files found")
                h_log.create_log(5, "speech_recognizer.__job_loop", f"Attempting to get files from database queue")
                db_result, db_content = h_db.get_colletion_item_sorted("ap_results",additional_query={"attempts":{"$lt":3}},sort_field="timestamp",ammount_of_items=20)
                if not db_result: #IF FAILED TO GET ENTRIES FROM DB
                    h_log.create_log(2, "speech_recognizer.__job_loop", f"Failed to get files from database queue. Reason: {str(db_content)}")
                    h_log.create_log(4, "speech_recognizer.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: NOK. Sleeptime before next iteration: {self._job_error_counter*10}. Time extended due to NOK")
                    time.sleep(self._job_error_counter*10)
                    self._job_loop_counter+=1
                    self._job_error_counter+=1
                    continue
                if len(db_content) == 0: #IF QUEUE IS EMPTY
                    h_log.create_log(5, "speech_recognizer.__job_loop",f"Successfully got respond from database queue. No files return, queue is empty")
                    h_log.create_log(4, "speech_recognizer.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: OK. Sleeptime before next iteration: 60.")
                    time.sleep(60)
                    self._job_loop_counter+=1
                h_log.create_log(5, "speech_recognizer.__job_loop",f"Successfully got respond from database queue. {len(db_content)} entries cached")
                self._job_chached_queue = db_content
                h_log.create_log(4, "speech_recognizer.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: OK")
                self._job_loop_counter+=1
                continue
            '''
            SECTION: RECOGNIZE
            '''
            file = self._job_chached_queue.pop(1)
            h_log.create_log(5,"speech_recognizer.__job_loop", f"Passing file {file} to recognizer object")
            recognizer = Azure(azure_api_key=self._job_configuration['azure_api_key'],
                               azure_region=self._job_configuration['azure_region'],
                               azure_language=self._job_configuration['azure_language'],
                               audio_path=file['path'],
                               timeout=self._job_configuration['azure_timeout'])
            recognition_result, recognition_content = recognizer.transcribe()
            if not recognition_result: #IF FAILED TO RECOGNIZE -> INCREASE ATTEMPTS IN DB
                h_log.create_log(2, "speech_recognizer.__job_loop", f"Failed to regonize file {file}. Reason: {str(recognition_content)}")
                attemp_counter = file['attempts']
                attemp_counter += 1
                h_log.create_log(5, "speech_recognizer.__job_loop", f"Attempting to increase 'attempts' filed for file {file} in database")
                update_result, update_content = h_db.change_kv_pair("ap_results",{"_id":ObjectId(file['id'])},"attempts",attemp_counter)
                if not update_result: #IF FAILED TO INCREASE ATTEMPTS FIELD
                    h_log.create_log(1, "speech_recognizer.__job_loop", f"Failed to increase 'attempts' field for file {file} in database. Reason: {str(update_content)}")
                    h_log.create_log(4, "speech_recognizer.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: NOK")
                    self._job_loop_counter+=1
                    self._job_error_counter+=1
                    continue
                h_log.create_log(5, "speech_recognizer.__job_loop", f"Successfully increased 'attempts' filed for file {file} in database")
                h_log.create_log(4, "speech_recognizer.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: OK")
                self._job_loop_counter+=1
                continue
            '''
            SECTION: SAVE RESULTS IN DB
            '''
            h_log.create_log(5, "speech_recognizer.__job_loop", f"Attempting to save recognition result in database")
            db_insert_result, db_insert_content = h_db.insert_one("sr_results",{"path":file['path'],"result":recognition_content})
            if not db_insert_result:
                h_log.create_log(2, "speech_recognizer.__job_loop", f"Failed to save recognition result in database. File {file['path']} will not be deleted from 'ap_results' queue. Re-recognition will be attempted after cache reload. Reason {str(db_insert_content)}")
                h_log.create_log(4, "speech_recognizer.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: NOK. Sleeptime before next iteration: {self._job_error_counter*10}. Time extended due to NOK")
                time.sleep(self._job_error_counter*10)
                self._job_loop_counter+=1
                self._job_error_counter+=1
                continue
            h_log.create_log(5, "speech_recognizer.__job_loop", f"Successfully saved recognition result in database")

            h_log.create_log(5, "speech_recognizer.__job_loop", f"Attempting to delete already recognized file {file} entry from database 'ap_results' queue")
            db_pop_result, db_pop_content = h_db.delete_collection("ap_results",{"_id":ObjectId(file['id'])})
            if not db_pop_result:
                h_log.create_log(2, "speech_recognizer.__job_loop", f"Failed to delete already recognized file {file} entry from database 'ap_results' queue. This database error will lead to unnecesary re-recognition of this file. Reason: {str(db_pop_content)}")
                h_log.create_log(4, "speech_recognizer.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: NOK. Sleeptime before next iteration: {self._job_error_counter*10}. Time extended due to NOK")
                time.sleep(self._job_error_counter*10)
                self._job_loop_counter+=1
                self._job_error_counter+=1
                continue   

            h_log.create_log(4, "speech_recognizer.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: OK")
            self._job_loop_counter+=1
            
         

