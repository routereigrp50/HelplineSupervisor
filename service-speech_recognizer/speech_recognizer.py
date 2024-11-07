from handlers.logging import Logging as h_log
from handlers.database import Database as h_db
from handlers.azure import Azure
from shared.tools.pydantic_models import SpeechRecognizerConfiguration
from shared.tools.decorators import retry
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        self._job_cached_queue = []
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
            if not self._job_cached_queue: #IF THERE ARE NO CACHED ENTRIES
                h_log.create_log(5, "speech_recognizer.__job_loop", f"No cached files found")
                h_log.create_log(5, "speech_recognizer.__job_loop", f"Attempting to get files from database queue")
                db_result, db_content = h_db.get_colletion_item_sorted("ap_results",additional_query={"attempts":{"$lt":3}},sort_field="timestamp",ammount_of_items=self._job_configuration['azure_concurrent_connections']*10)
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
                    continue
                h_log.create_log(5, "speech_recognizer.__job_loop",f"Successfully got respond from database queue. {len(db_content)} entries cached")
                self._job_cached_queue = db_content
                h_log.create_log(4, "speech_recognizer.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: OK")
                self._job_loop_counter+=1
                continue
            '''
            SECTION: RECOGNIZE
            '''
            #CHCEK IF DESIRED CONNECTION AMMOUNT ISNT BIGGER THAN CACHED QUEUE
            connection_ammount = self._job_configuration['azure_concurrent_connections']
            if int(self._job_configuration['azure_concurrent_connections']) > len(self._job_cached_queue):
                h_log.create_log(3, "speech_recongizer.__job_loop", f"Desired connection ammount is bigger than cached queue. Changing connection ammount for this iteration to {len(self._job_cached_queue)}")
                connection_ammount = len(self._job_cached_queue)
            
            #PREPARE FILES
            local_file_q = []
            for _ in range(connection_ammount):
                file = self._job_cached_queue.pop(0)
                local_file_q.append(file)
            
            #RECOGNIZE SEGMENT
            with ThreadPoolExecutor(max_workers=self._job_configuration['azure_concurrent_connections']) as executor:
                futures = []
                results = []
                for element in local_file_q:
                    thread = executor.submit(self._call_azure, element)
                    futures.append(thread)
                    h_log.create_log(5, "speech_recognizer.__job_loop", f"Creating recognition thread for {element['path']}")
                for future in as_completed(futures):
                    results.append(future.result())
                    h_log.create_log(4, "speech_recognizer.__job_loop", f"Recognition thread ended job. Acutal stuts: {len(results)}/{len(local_file_q)}")
            '''
            SECTION: SAVE RESULTS IN DB
            '''
            for result in results:
                recognition_element, recognition_result, recognition_content = result
                current_timestamp = datetime.now(timezone.utc)
                h_log.create_log(5, "speech_recognizer.__job_loop", f"Attempting to update database information for {recognition_element}")
                if not recognition_result:
                    #BRIEF UPDATE
                    db_brief_fail_result, db_brief_fail_content = h_db.insert_one("sr_results_brief", {"path":recognition_element['path'],"timestamp":current_timestamp,"status":"Failed","reason":str(recognition_content)})
                    if not db_brief_fail_result:
                        h_log.create_log(2, "speech_recognizer._joob_loop", f"Failed to save recognition brief informations in database for entry {recognition_element}. Reason: {str(db_brief_fail_content)}")
                        self._job_error_counter += 1
                    #KV CHANGE += ATTEMPTS
                    attempt_counter = recognition_element['attempts']
                    attempt_counter += 1
                    kv_update_result, kv_update_content = h_db.change_kv_pair("ap_results",{"_id":ObjectId(recognition_element['id'])},"attempts",attempt_counter)
                    if not kv_update_result:
                        h_log.create_log(2, "speech_recognizer.__job_loop", f"Failed to update 'attempts' counter in database for entry {recognition_element}. This will lead to unplanned extra recognition attempt for this entry. Reason: {str(kv_update_content)}")
                        self._job_error_counter += 1
                else:
                    #BRIEF UPDATE
                    db_brief_succ_result, db_brief_succ_content = h_db.insert_one("sr_results_brief", {"path":recognition_element['path'],"result":recognition_content,"timestamp":current_timestamp,"status":"Success"})
                    if not db_brief_succ_result:
                        h_log.create_log(2, "speech_recognizer._joob_loop", f"Failed to save recognition brief informations in database for entry {recognition_element}. Reason: {str(db_brief_succ_content)}")
                        self._job_error_counter += 1
                    #CONTENT UPDATE
                    db_insert_result, db_insert_content = h_db.insert_one("sr_results",{"path":recognition_element['path'],"result":recognition_content,"timestamp":current_timestamp})
                    if not db_insert_result:
                        h_log.create_log(2, "speech_recognizer.__job_loop", f"Failed to save recognition result in database for entry {recognition_element}. Reason: {str(db_insert_content)}")
                        self._job_error_counter += 1
                        h_log.create_log(5, "speech_recognizer.__job_loop", f"Ended of database information update for {recognition_element}")
                        continue
                        #IF RESULT NOT SAVED CONTINUE LOOP ITERATION AND DONT DELETE THIS ENTRY FORM Q TO AVOID MISSING FILE
                    #DELETE FROM Q
                    db_pop_result, db_pop_content = h_db.delete_collection("ap_results",{"_id":ObjectId(recognition_element['id'])})
                    if not db_pop_result:
                        h_log.create_log(2, "speech_recognizer._joob_loop", f"Failed to delete entry from queue 'ap_results'. Element: {recognition_element}. Reason: {str(db_pop_content)}")
                        self._job_error_counter += 1
                h_log.create_log(5, "speech_recognizer.__job_loop", f"Ended of database information update for {recognition_element}")

            h_log.create_log(4, "speech_recognizer.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: OK")
            self._job_loop_counter+=1
            
         
    def _call_azure(self, file_dict: dict) -> tuple:
        """
        FUNCTION: CALL TO AZURE INTERFACE
        """
        try:
            recognizer = Azure(azure_api_key=self._job_configuration['azure_api_key'],
                            azure_region=self._job_configuration['azure_region'],
                            azure_language=self._job_configuration['azure_language'],
                            audio_path=file_dict['path'],
                            timeout=self._job_configuration['azure_timeout'])
            recognition_result, recognition_content = recognizer.transcribe()
            return (file_dict, recognition_result, recognition_content)
        except Exception as e:
            return (file_dict, False, str(e))#
