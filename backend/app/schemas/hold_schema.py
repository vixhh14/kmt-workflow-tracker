from pydantic import BaseModel

class HoldRequest(BaseModel):
    reason: str
