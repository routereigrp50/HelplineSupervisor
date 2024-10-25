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



class SpeechRecognizer:
    def __init__(self, api_configuration: dict) -> None:
        pass