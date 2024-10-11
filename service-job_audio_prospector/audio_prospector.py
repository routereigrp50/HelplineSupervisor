from handlers.database import Database as h_db
from handlers.logging import Logging as h_log



class AudioProspector:
    def __init__(self, conf_audio_file_path: str, audio_file_extension: str, scanning_interval: int) -> tuple:
        self.conf_audio_file_path = conf_audio_file_path
        self.conf_audio_file_extension = audio_file_extension
        self.conf_scanning_interval = scanning_interval
        self.status = "Idle"
        self.health = "Healthy"
        self.db_push_status, self.db_push_potential_error = h_db.insert_one('jobs',{"status":self.status,"health":self.health,"configuration":{"audio_file_path":self.conf_audio_file_path,"audio_file_extension":self.conf_audio_file_extension,"scanning_interval":self.conf_scanning_interval}})
        if not self.db_push_status:
            return (False, str(self.db_push_potential_error))
        return (True, None)

    def start(self) -> None:
        print("START")

    def stop(self) -> None:
        print("STOP")
    