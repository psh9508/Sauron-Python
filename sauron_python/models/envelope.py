from pydantic import BaseModel, Field

class Envelope(BaseModel):
    id: str
    endpoint: str = Field(default="http://127.0.0.1:8002/test", description="Sauron endpoint")
    payload: dict