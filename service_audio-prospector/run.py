from handlers.logging import Logging as h_log
from handlers.database import Database as h_db
from audio_prospector import AudioProspector
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
    Pass configuration to handlers sections
    '''
    h_log.create_log(4, "run.__main__", f"Attempting to pass configuration to handlers")
    try:
        h_log.set_debug(configuration["logging"]['local']['audio_prospector']["debugging"]) if configuration["logging"]['local']['audio_prospector']["debugging"] else h_log.set_debug(configuration['logging']['global']['debugging'])
        h_log.set_stdout_console(configuration["logging"]['local']['audio_prospector']["stdout"]['console']['state']) if configuration["logging"]['local']['audio_prospector']["stdout"]['console']['state'] else h_log.set_stdout_console(configuration['logging']['global']['stdout']['console']['state'])
        h_log.set_stdout_db(configuration["logging"]['local']['audio_prospector']["stdout"]['database']['state'],configuration['database']['mongo_db_uri']) if configuration["logging"]['local']['audio_prospector']["stdout"]['database']['state'] else h_log.set_debug(configuration['logging']['global']['stdout']['database']['state'],configuration['database']['mongo_db_uri'])
        h_log.set_stdout_file(configuration["logging"]['local']['audio_prospector']["stdout"]['file']['state']) if configuration["logging"]['local']['audio_prospector']["stdout"]['file']['state'] else h_log.set_stdout_file(configuration['logging']['global']['stdout']['file']['state'])
        h_log.set_stdout_file_path(configuration["logging"]['local']['audio_prospector']["stdout"]['file']['file_path']) if configuration["logging"]['local']['audio_prospector']["stdout"]['file']['file_path'] else h_log.set_stdout_file(configuration['logging']['global']['stdout']['file']['file_path'])
        h_db.set_uri(configuration['database']['mongo_db_uri'])
    except Exception as e:
        h_log.create_log(2, "run.__main__", f"Failed to pass configuration to handlers. Reason {str(e)}")
        h_log.create_log(1, "run.__main__", f"Failed to start service audio_prospector")
        time.sleep(5), quit()
    h_log.create_log(4, "run.__main__", f"Successfully passed confituration to handlers")
    '''
    Create job object and run :)
    '''
    ap = AudioProspector(configuration['api']['audio_prospector'])

