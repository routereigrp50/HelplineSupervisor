from handlers.logging import Logging as h_log
from handlers.database import Database as h_db
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from bson import ObjectId, errors



app = FastAPI(title="HelplineSupervisor - API Gateway", version="A0.1")