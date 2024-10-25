from pydantic import BaseModel
from typing import Literal, Optional, List

class AudioProspectorConfiguration(BaseModel):
    path: str
    audio_extension: Literal['wav']
    scanning_interval: int
