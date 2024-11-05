from handlers.logging import Logging as h_log
from handlers.database import Database as h_db
from tools.pydantic_models import ConversationPeeperConfiguration
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
import requests
import json




class ConversationPeeper:
    def __init__(self, api_configuration: dict) -> None:
        '''
        API VARS
        '''
        self._api = FastAPI(title="Conversation Peeper", version="v0.2",openapi_tags=[{"name":"Monitoring"},{"name":"Operations"}]) 
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
        h_log.create_log(5, "conversation_peeper._api_start", "Passing configuration to api object and startning api server")
        try:
            config = uvicorn.Config(self._api, host=api_configuration['ip'], port=api_configuration['port'], log_level="warning")
            server = uvicorn.Server(config)
            server.run()
        except Exception as e:
            h_log.create_log(1, "conversation_peeper._api_start", f"Failed to start api server. Reason {str(e)}")
            self.status['api']['status'] = "FAILED"
            time.sleep(3), quit()
    
    def _api_routing(self) -> None:
        '''
        FUNCTION: API ROUTING
        '''
        @self._api.get("/api/conversationpeeper/status",tags=['Monitoring'])
        async def get_job_status() -> JSONResponse:
            h_log.create_log(4, "conversation_peeper._api_routing", f"S: API hit no. {self._api_hit_counter} get /api/conversationpeeper/status")
            h_log.create_log(4, "conversation_peeper._api_routing", f"EOK: API hit no. {self._api_hit_counter} get /api/conversationpeeper/status")
            self._api_hit_counter+=1
            return JSONResponse(content={"status":"OK","content":self.status},status_code=200)

        @self._api.post("/api/conversationpeeper/start",tags=['Operations'])
        async def start_job(post_body: ConversationPeeperConfiguration) -> JSONResponse:
            h_log.create_log(4, "conversation_peeper._api_routing", f"S: API hit no. {self._api_hit_counter} post /api/conversationpeeper/start")
            job_config = post_body.model_dump()
            start_status, start_error_msg = self._job_start(job_config)
            if not start_status:
                h_log.create_log(3, "conversation_peeper._api_routing", f"ENOK: API hit no. {self._api_hit_counter} post /api/conversationpeeper/start")
                self._api_hit_counter+=1
                return JSONResponse(content={"status":"NOK","content":str(start_error_msg)},status_code=400)
            h_log.create_log(4, "conversation_peeper._api_routing", f"EOK: API hit no. {self._api_hit_counter} post /api/conversationpeeper/start")
            self._api_hit_counter+=1
            return JSONResponse(content={"status":"OK", "content":""},status_code=201)
        
        @self._api.post("/api/conversationpeeper/stop",tags=['Operations'])
        async def stop_job() -> JSONResponse:
            h_log.create_log(4, "conversation_peeper._api_routing", f"S: API hit no. {self._api_hit_counter} post /api/conversationpeeper/stop")
            stop_status, stop_error_msg = self._job_stop()
            if not stop_status:
                h_log.create_log(3, "conversation_peeper._api_routing", f"ENOK: API hit no. {self._api_hit_counter} post /api/conversationpeeper/stop")
                self._api_hit_counter+=1
                return JSONResponse(content={"status":"NOK","content":str(stop_error_msg)},status_code=400)
            h_log.create_log(4, "conversation_peeper._api_routing", f"EOK: API hit no. {self._api_hit_counter} post /api/conversationpeeper/stop")
            self._api_hit_counter+=1
            return JSONResponse(content={"status":"OK","content":""},status_code=201)

    def _job_start(self, job_configuration: dict) -> tuple:
        '''
        FUNCTION: RUN JOB INTERFACE
        '''
        h_log.create_log(4, "conversation_peeper._job_start", f"Attempting to start job with configuration: {job_configuration}")
        h_log.create_log(5, "conversation_peeper._job_start", f"Attempting to verify current job status")
        if self.status['job']['status'] == "RUNNING":
            h_log.create_log(2, "conversation_peeper._job_start", f"Current job status is 'RUNNING'")
            h_log.create_log(2, "conversation_peeper._job_start", f"Failed to start job. Reason: Job is already RUNNING")
            return (False, "Job is already RUNNING")
        h_log.create_log(5, "conversation_peeper._job_start", f"Current job status is {self.status['job']['status']}")
        h_log.create_log(5, "conversation_peeper._job_start", f"Creating job thread")
        thread = threading.Thread(target = self.__job_loop, args = ())
        h_log.create_log(5, "conversation_peeper._job_start", f"Starting job thread")
        self._job_run_indicator = True
        thread.start()
        self.status['job']['status'] = "RUNNING"
        self.status['job']['configuration'] = job_configuration
        self._job_configuration = job_configuration
        h_log.create_log(4, "conversation_peeper._job_start", f"Successfully started job with configuration: {job_configuration}")
        return (True, None)

    def _job_stop(self) -> tuple:
        '''
        FUNCTION: STOP JOB INTERFACE
        '''
        h_log.create_log(4, "conversation_peeper._job_stop", f"Attempting to stop job")
        h_log.create_log(5, "conversation_peeper._job_stop", f"Attempting to verify current job status")
        if self.status['job']['status'] != "RUNNING":
            h_log.create_log(3, "conversation_peeper._job_stop", f"Current job statis is not 'RUNNING'")
            h_log.create_log(3, "conversation_peeper._job_stop", f"Failed to stop job. Reason: Job is not RUNNING")
            return (False, "Job is not RUNNING")
        h_log.create_log(5, "conversation_peeper._job_stop", f"Current job status is {self.status['job']['status']}")
        h_log.create_log(5, "conversation_peeper._job_stop", f"Setting job flag indicator to False")
        self._job_run_indicator = False
        self._job_loop_counter = 1
        self._job_error_counter = 1
        self.status['job']['status'] = "IDLE"
        self.status['job']['configuration'] = {}
        h_log.create_log(4, "conversation_peeper._job_stop", f"Successfully stoped job")
        return (True, None)

    def __job_loop(self) -> None:
        '''
        FUNCTION: CORE JOB FUNCTION
        '''
        while self._job_run_indicator:
            h_log.create_log(4, "conversation_peeper.__job_loop", f'Starting loop iteration no. {self._job_loop_counter}')
            '''
            SECTION: GET FILE FROM Q
            '''
            if not self._job_cached_queue: #IF THERE ARE NO CACHED ENTRIES
                h_log.create_log(5, "conversation_peeper.__job_loop", f"No cached files found")
                h_log.create_log(5, "conversation_peeper.__job_loop", f"Attempting to get files from database queue")
                db_result, db_content = h_db.get_colletion_item_sorted("sr_results",sort_field="timestamp",ammount_of_items=20)
                if not db_result: #IF FAILED TO GET ENTRIES FROM DB
                    h_log.create_log(2, "conversation_peeper.__job_loop", f"Failed to get files from database queue. Reason: {str(db_content)}")
                    h_log.create_log(4, "conversation_peeper.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: NOK. Sleeptime before next iteration: {self._job_error_counter*10}. Time extended due to NOK")
                    time.sleep(self._job_error_counter*10)
                    self._job_loop_counter+=1
                    self._job_error_counter+=1
                    continue
                if len(db_content) == 0: #IF QUEUE IS EMPTY
                    h_log.create_log(5, "conversation_peeper.__job_loop",f"Successfully got respond from database queue. No files return, queue is empty")
                    h_log.create_log(4, "conversation_peeper.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: OK. Sleeptime before next iteration: 60.")
                    time.sleep(60)
                    self._job_loop_counter+=1
                    continue
                h_log.create_log(5, "conversation_peeper.__job_loop",f"Successfully got respond from database queue. {len(db_content)} entries cached")
                self._job_cached_queue = db_content
                h_log.create_log(4, "conversation_peeper.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: OK")
                self._job_loop_counter+=1
                continue
            '''
            SECTION: PEEP
            '''
            file = self._job_cached_queue.pop(0)
            h_log.create_log(5, "conversation_peeper.__job_loop",f"Atempting to peep into {file['path']}")
            call_result, call_content = self._call_azure_api(file['result'])
            if not call_result:
                h_log.create_log(2, "conversation_peeper.__job_loop", f"Failed to peep file {file['path']}, Reason: {str(call_content)}")
                h_log.create_log(4, "conversation_peeper.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: NOK. Sleeptime before next iteration: {self._job_error_counter*10}. Time extended due to NOK")
                time.sleep(self._job_error_counter*10)
                self._job_loop_counter+=1
                self._job_error_counter+=1
                continue
            h_log.create_log(5, "conversation_peeper.__job_loop", f"Successfully peeped into {file['path']}")
            '''
            SECTION: SAVE RESULTS IN DB
            '''
            h_log.create_log(5, "conversation_peeper.__job_loop", f"Attempting to save recognition result in database")
            current_timestamp = datetime.now(timezone.utc)
            db_insert_result, db_insert_content = h_db.insert_one("cp_results",{"path":file['path'],"timestamp":current_timestamp,"result":call_content})
            if not db_insert_result:
                h_log.create_log(2, "conversation_peeper.__job_loop", f"Failed top save peep result in database")
                h_log.create_log(4, "conversation_peeper.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: NOK. Sleeptime before next iteration: {self._job_error_counter*10}. Time extended due to NOK")
                time.sleep(self._job_error_counter*10)
                self._job_loop_counter+=1
                self._job_error_counter+=1
                continue
            h_log.create_log(5, "conversation_peeper.__job_loop", f"Successfully saved peep result in database")

            h_log.create_log(5, "conversation_peeper.__job_loop", f"Attempting to delete already rated file {file['path']} from database 'sr_results'")
            db_pop_result, db_pop_content = h_db.delete_collection("sr_results", {"_id":ObjectId(file['id'])})
            if not db_pop_result:
                h_log.create_log(2, "conversation_peeper.__job_loop", f"Failed to delete already rated file {file['path']} from database. This will lead to re-evaluation of this file in future.  Reason: {str(db_pop_content)}")
                h_log.create_log(4, "conversation_peeper.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: NOK. Sleeptime before next iteration: {self._job_error_counter*10}. Time extended due to NOK")
                time.sleep(self._job_error_counter*10)
                self._job_loop_counter+=1
                self._job_error_counter+=1
                continue  
            h_log.create_log(5, "conversation_peeper.__job_loop", f"Successfullt deleted already rated file {file['path']} from database 'sr_results'")

            h_log.create_log(4, "speech_recognizer.__job_loop", f"End of loop iteration no. {self._job_loop_counter} with status: OK")
            self._job_loop_counter+=1
            
                        
    def _call_azure_api(self, content: str) -> tuple:
        '''
        FUNCTION: CALL TO AZURE INTERFACE
        '''
        headers = {
            "Content-Type": "application/json",
            "api-key": self._job_configuration['azure_api_key'],
            }
        payload = {
            "messages": [
                {
                "role": "system",
                "content": r"Jesteś asystentem który otrzymuje transkrypcje z rozmowy na infolinii. Twoim zadaniej jest ocena dwóch aspektów tej rozmowy. Pierwszy aspekt to jakość pracy konsultanta infolini - sprawdź czy konsultant był uprzejmy, czy wyrażał chęć pomocy dzwoniącemu i ogólną jakość rozmowy. Twoja odpowiedź musi być jedną z tych opcji: 'Pozytywna', 'Neutralna', 'Negatywna', 'Niemożliwa do weryfikacji'. Do każdej opcji dodaj argumentowanie dlaczego w taki sposób oceniłeś rozmowę. Drugi aspekt to aspekt bezpieczeństwa. Sprawdź czy w rozmowie nie było żadnej próby wyłudzania danych bądź innych wrażliwych informacji. Tutaj zwróć jedną z odpowiedzi - 'Brak podejrzeń', 'Podejrzenie próby wyłudzenia'. Swoją odpowiedź zwróć w formacie json. {'ocena_jakosci':<twoja_ocena>,'argumentacja_jakosci':<twoja_argumentacja>,'ocena_bezpieczenstwa':<twoja_ocena>,'argumentacja_bezpieczenstwa':<twoja_argumentacja>}"
                },
                {
                "role": "user",
                "content": content
                }
            ],
            "temperature": 0.7,
            "top_p": 0.95,
            "max_tokens": 800
            }
        try:
            h_log.create_log(5, "conversation_peeper._call_azure_api", "Calling Azure API")
            response = requests.post(self._job_configuration['azure_open_ai_endpoint'],headers=headers,json=payload)
            
            if response.status_code != 200:
                h_log.create_log(2, "conversation_peeper._call_azure_api", f"Calling Azure API ended with error {response.status_code}")
                return (False, f"Error with status code {response.status_code}")

            h_log.create_log(5, "conversation_peeper._call_azure_api", f"Successfully received answer from Aazure API")
            json_content = response.json()
            desired_content = json_content['choices'][0]['message']['content']
            desired_json_content = json.loads(desired_content)
            return (True, desired_json_content)
        except KeyError:
            h_log.create_log(2, "conversation_peeper._call_azure_api", f"Calling Azure API ended with error. Received content in unexpected format.")
            return (False, "Received content in unexpected format")
        except json.JSONDecodeError:
            h_log.create_log(2, "conversation_peeper._call_azure_api", "Failed to parse JSON content in API response")
            return (False, "Failed to parse JSON content in API response")
        except Exception as e:
            h_log.create_log(2, "conversation_peeper._call_azure_api", f"Calling Azure API ended with error {str(e)}")
            return (False, str(e))