from handlers.logging import Logging as h_log
from handlers.database import Database as h_db
from audio_prospector import AudioProspector as audio_prospector
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from bson import ObjectId, errors



app = FastAPI(title="HelplineSupervisor - job audio prospector", version="A0.1")

@app.post("/job/run")
async def run_audio_prospector():
    
