from handlers.logging import Logging as h_log
from handlers.database import Database as h_db
from handlers.api import app as h_api
import json
from jsonschema import validate, ValidationError, SchemaError
import time
import uvicorn



if __name__ == "__main__":
    h_log.create_log(4, "run.__main__", "Attempting to start service api_gateway")
    
    h_log.create_log(4, "run.__main__", "Attempting to read configuration file")
    try:
        with open('./config.json', 'r') as file:
            configuration = json.load(file)
    except FileNotFoundError as e:
        h_log.create_log(2, "run.__main__", f"Failed to read configuration file. Reason: {str(e)}")
        h_log.create_log(1, "run.__main__", "Failed to start service api_gateway")
        time.sleep(5), quit()
    except PermissionError as e:
        h_log.create_log(2, "run.__main__", f"Failed to read configuration file. Reason: {str(e)}")
        h_log.create_log(1, "run.__main__", "Failed to start service api_gateway")
        time.sleep(5), quit()
    except Exception as e:
        h_log.create_log(2, "run.__main__", f"Failed to read configuration file. Reason: {str(e)}")
        h_log.create_log(1, "run.__main__", "Failed to start service api_gateway")
        time.sleep(5), quit()
    h_log.create_log(4, "run.__main__", "Successfully read configuration file")

    h_log.create_log(4, "run.__main__", "Attempting to validate configuration file")
    config_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "api": {
            "type": "object",
            "properties": {
                "ip": {
                "type": "string",
                "format": "ipv4"
                },
                "port": {
                "type": "integer",
                "minimum": 1,
                "maximum": 65535
                }
            },
            "required": ["ip", "port"]
            },
            "database": {
            "type": "object",
            "properties": {
                "mongo_db_uri": {
                "type": "string",
                "pattern": "^mongodb\\+srv://.+$"
                }
            },
            "required": ["mongo_db_uri"]
            },
            "logging": {
            "type": "object",
            "properties": {
                "debugging": {
                "type": "boolean"
                },
                "stdout": {
                "type": "object",
                "properties": {
                    "console": {
                    "type": "object",
                    "properties": {
                        "state": {
                        "type": "boolean"
                        }
                    },
                    "required": ["state"]
                    },
                    "file": {
                    "type": "object",
                    "properties": {
                        "state": {
                        "type": "boolean"
                        },
                        "file_path": {
                        "type": "string",
                        "format": "uri-reference"
                        }
                    },
                    "required": ["state", "file_path"]
                    },
                    "database": {
                    "type": "object",
                    "properties": {
                        "state": {
                        "type": "boolean"
                        },
                        "mongo_db_uri": {
                        "type": "string",
                        "pattern": "^mongodb\\+srv://.+$"
                        }
                    },
                    "required": ["state", "mongo_db_uri"]
                    }
                },
                "required": ["console", "file", "database"]
                }
            },
            "required": ["debugging", "stdout"]
            }
        },
        "required": ["api", "database", "logging"]
        }
    try:
        validate(instance=configuration, schema=config_schema)
    except ValidationError as e:
        h_log.create_log(2, "run.__main__", f"Failed to validate configuration file. Reason: {str(e)}")
        h_log.create_log(1, "run.__main__", "Failed to start service api_gateway")
        time.sleep(5), quit()
    h_log.create_log(4, "run.__main__", f"Successfully validated configuratuin file")
    
    h_log.create_log(4, "run.__main__", f"Attempting to pass configuration to handlers")
    h_log.set_debug(configuration["logging"]["debugging"])
    h_log.set_stdout_console(configuration["logging"]["stdout"]["console"]["state"])
    h_log.set_stdout_file(configuration["logging"]["stdout"]["file"]["state"])
    h_log.set_stdout_file_path(configuration["logging"]["stdout"]["file"]["file_path"])
    h_log.set_stdout_db(configuration["logging"]["stdout"]["database"]["state"],configuration["logging"]["stdout"]["database"]["mongo_db_uri"])
    h_db.set_uri(configuration['database']['mongo_db_uri'])
    h_log.create_log(4, "run.__main__", f"Successfully passed configuraiton to handlers")

    h_log.create_log(4, "run.__main__", f"Attempting to initialize DB connection")
    db_init_status, db_init_potential_error = h_db.initialize()
    if not db_init_status:
        h_log.create_log(2, "run.__main__", f"Failed to initialize DB connection. Reason: {str(db_init_potential_error)}")
        h_log.create_log(1, "run.__main__", f"Failed to start service api_gateway")
        time.sleep(5), quit()
    h_log.create_log(4, "run.__main__", f"Successfully initialized DB connection")

    h_log.create_log(4, "run.__main__", f"Successfully started service api_gateway")
    uvicorn.run(h_api, host = configuration['api']['ip'], port = configuration['api']['port'])
   