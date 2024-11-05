from pydantic import BaseModel
from typing import Literal, Optional, List

class AudioProspectorConfiguration(BaseModel):
    path: str
    audio_extension: Literal['wav']
    scanning_interval: int

class ConversationPeeperConfiguration(BaseModel):
    azure_api_key: str
    azure_open_ai_endpoint: str

class SpeechRecognizerConfiguration(BaseModel):
    azure_api_key: str
    azure_region: str
    azure_language: str
    azure_timeout: int