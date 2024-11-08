from handlers.logging import Logging as h_log
from handlers.database import Database as h_db
from speech_recognizer import SpeechRecognizer
import json
import time



if __name__ == "__main__":
    h_log.create_log(4, "run.__main__", "Attempting to start service speech_recognizer")
    '''
    SECTION: READ CONFITURATION FILE
    '''
    h_log.create_log(4, "run.__main__", "Attempting to read configuration file")
    try:
        with open('./shared/config.json', 'r') as file:
            configuration = json.load(file)
    except FileNotFoundError as e:
        h_log.create_log(2, "run.__main__", f"Failed to read configuration file. Reason: {str(e)}")
        time.sleep(5), quit()
    except PermissionError as e:
        h_log.create_log(2, "run.__main__", f"Failed to read configuration file. Reason: {str(e)}")
        h_log.create_log(1, "run.__main__", "Failed to start service speech_recognizer")
        time.sleep(5), quit()
    except Exception as e:
        h_log.create_log(2, "run.__main__", f"Failed to read configuration file. Reason: {str(e)}")
        h_log.create_log(1, "run.__main__", "Failed to start service speech_recognizer")
        time.sleep(5), quit()
    h_log.create_log(4, "run.__main__", "Successfully read configuration file")
    '''
    SECTION: VALIDATE CONFIGURATION FILE
    '''
    #Configuration validation feature placeholder. Need to be added before pushing to production stage
    '''
    SECTION: PASS CONFIGURATION TO HANDLERS
    LOGIC BEHIND IS SIMPLE, TRY TO PASS LOCAL CONFIG FROM CONFIG FILE, IF ERROR = NO LOCAL CONFIG AVAIBLE. THEN PASS GLOBAL
    '''
    h_log.create_log(4, "run.__main__", f"Attempting to pass configuration to handlers")
    try:
        try: h_log.set_debug(configuration["logging"]['local']['speech_recognizer']["debugging"]) 
        except KeyError: h_log.set_debug(configuration['logging']['global']['debugging']) 

        try: h_log.set_stdout_console(configuration["logging"]['local']['speech_recognizer']["stdout"]['console']['state']) 
        except KeyError: h_log.set_stdout_console(configuration['logging']['global']['stdout']['console']['state'])

        try: h_log.set_stdout_db(configuration["logging"]['local']['speech_recognizer']["stdout"]['database']['state'],configuration['database']['mongo_db_uri']) 
        except KeyError: h_log.set_stdout_db(configuration['logging']['global']['stdout']['database']['state'],configuration['database']['mongo_db_uri'])

        try: h_log.set_stdout_file_path(configuration["logging"]['local']['speech_recognizer']["stdout"]['file']['file_path']) 
        except: h_log.set_stdout_file_path(configuration['logging']['global']['stdout']['file']['file_path'])

        try: h_log.set_stdout_file(configuration["logging"]['local']['speech_recognizer']["stdout"]['file']['state']) 
        except KeyError: h_log.set_stdout_file(configuration['logging']['global']['stdout']['file']['state'])

        h_db.set_uri(configuration['database']['mongo_db_uri'])
        initialization_status, initialization_content = h_db.initialize() 
        if not initialization_status:
            raise
    except Exception as e:
        h_log.create_log(2, "run.__main__", f"Failed to pass configuration to handlers")
        h_log.create_log(1, "run.__main__", f"Failed to start service speech_recognizer")
        time.sleep(5), quit()
    h_log.create_log(4, "run.__main__", f"Successfully passed configuration to handlers")
    '''
    SECTION: CREATE AND RUN JOB
    '''
    h_log.create_log(4, "run.__main__", f"Successfully started service speech_recognizer")
    sr = SpeechRecognizer(configuration['api']['speech_recognizer'])