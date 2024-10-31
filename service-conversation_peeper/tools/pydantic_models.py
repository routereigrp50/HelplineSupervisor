from pydantic import BaseModel
from typing import Literal, Optional, List

class ConversationPeeperConfiguration(BaseModel):
    azure_api_key: str
    azure_open_ai_endpoint: str
