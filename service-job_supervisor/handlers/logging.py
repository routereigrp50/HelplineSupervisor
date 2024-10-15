import datetime
import pymongo



class Logging:
    _debug = False
    _stdout_console = True
    _stdout_file = False
    _stdout_db = False
    _stdout_file_path = ""
    _db_private_client = None
    _service_name = "job_supervisor"

    @classmethod
    def create_log(cls, severity: int, announcer: str, log: str) -> None:
        match severity:
            case 1:
                severity_str = "CRIT"
            case 2:
                severity_str = "ERRO"
            case 3:
                severity_str = "WARN"
            case 4:
                severity_str = "INFO"
            case 5:
                severity_str = "DBUG"

        parsed_log = f"{cls._timestamp()} | {severity_str} @ Service: {cls._service_name} & Function: {announcer} | {log}" if cls._debug == True else f"{cls._timestamp()} | {severity_str} | {log}"
        
        if severity == 5 and cls._debug: #If severity is debug and debugging is enabled
            print(parsed_log) if cls._stdout_console else None
            cls._write_log_to_file(parsed_log) if cls._stdout_file else None
            cls._write_log_to_db({"timestamp":datetime.datetime.now(),"severity": severity_str, "service": cls._service_name, "function": announcer, "log": log}) if cls._stdout_db else None
        elif severity == 5 and not cls._debug: #If severity is debug and debugging is disabled
            pass
        else: #If severity is not debug
            print(parsed_log) if cls._stdout_console else None
            cls._write_log_to_file(parsed_log) if cls._stdout_file else None
            cls._write_log_to_db({"timestamp":datetime.datetime.now(),"severity": severity_str, "service": cls._service_name, "function": announcer, "log": log}) if cls._stdout_db else None
    
    @classmethod
    def set_debug(cls, state: bool) -> None:
        cls._debug = state
        cls.create_log(5,"handlers.logging.set_debug", f"Setting logging debug to {state}")

    @classmethod
    def set_stdout_console(cls, state: bool) -> None:
        cls.stdout_console = state
        cls.create_log(5,"handlers.logging.set_stdout_console", f"Setting logging stdout_console to {state}")

    @classmethod
    def set_stdout_file(cls, state: bool) -> None:
        cls._stdout_file = state
        cls.create_log(5,"handlers.logging.set_stdout_file", f"Setting logging stdout_file to {state}")
    
    @classmethod
    def set_stdout_file_path(cls, path: str) -> None:
        cls._stdout_file_path = path
        cls.create_log(5,"handlers.logging.set_stdout_file_path", f"Setting logging stdout_file_path to {path}")

    @classmethod 
    def set_stdout_db(cls, state: bool, db_uri: str = None) -> None:
        if state:
            cls._db_private_client = pymongo.MongoClient(db_uri)
            cls._stdout_db = state
        else:
            cls._stdout_db = state
            cls._db_private_client = None
        cls.create_log(5,"handlers.logging.set_stdout_db", f"Setting logging stdout_db to {state}")

    @classmethod
    def _timestamp(cls) -> str:
        current_time = datetime.datetime.now().strftime("20%y/%m/%d %H:%M:%S")
        return current_time

    @classmethod
    def _write_log_to_file(cls, log: str) -> None:
        try:
            with open(cls._stdout_file_path, "a") as file:
                file.write(f"{log}\n")
        except PermissionError as e:
            cls.set_stdout_file(False) #Disable logging to file in case of file writing error
            cls.create_log(2, "handlers.logging._write_log_to_file", f"Failed to write to log to file. Reason: 'Permission error'")
        except Exception as e:
            cls.set_stdout_file(False) #Disable logging to file in case of file writing error
            cls.create_log(3, "handlers.logging._write_log_to_file", f"Failed to write to log to file. Reason: '{str(e)}'")
            
    @classmethod
    def _write_log_to_db(cls, log: str) -> None:
        try:
            collection = cls._db_private_client['HelplineSupervisor']["logs"]
            collection.insert_one(log)
        except Exception as e:
            cls.set_stdout_db(False) #Disable logging to db in case of writing error
            cls.create_log(2,"handlers.logging._write_log_to_db", f"Failed to write log to database. Reason: '{str(e)}'")
