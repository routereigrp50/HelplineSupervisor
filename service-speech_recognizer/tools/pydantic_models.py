from pydantic import BaseModel
from typing import Literal, Optional, List

class SpeechRecognizerConfiguration(BaseModel):
    azure_api_key: str
    azure_region: str
    azure_language: str
    max_simultaneous_connections: int

