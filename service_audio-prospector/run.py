from handlers.logging import Logging as h_log
from handlers.database import Database as h_db
import json
import time



if __name__ == "__main__":
    h_log.create_log(4, "run.__main__", "Attempting to start service audio_prospector")
    '''
    Read configuration file section
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
        h_log.create_log(1, "run.__main__", "Failed to start service audio_prospector")
        time.sleep(5), quit()
    except Exception as e:
        h_log.create_log(2, "run.__main__", f"Failed to read configuration file. Reason: {str(e)}")
        h_log.create_log(1, "run.__main__", "Failed to start service audio_prospector")
        time.sleep(5), quit()
    h_log.create_log(4, "run.__main__", "Successfully read configuration file")
    '''
    Validate configuration file section
    '''
    #Configuration validation feature placeholder
    '''
    Pass configuration to handlers
    '''
    
