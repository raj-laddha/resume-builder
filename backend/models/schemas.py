from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime

class JobDescription(BaseModel):
    description: str

class UserProfileFile(BaseModel):
    filename: str
    content_type: str
    size: int
    content: str
    parsed_at: datetime

class SessionData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    websocket_handler: Any = None
    resume_team: Any = None
    user_profile: Optional[UserProfileFile] = None
    job_description: Optional[str] = None
    resume_store: Optional[dict] = None
    created_at: datetime
    last_updated: datetime

class DBSession(BaseModel):
    session_id: str
    created_at: datetime
    last_updated: datetime
    user_profile: Optional[UserProfileFile] = None
    job_description: Optional[str] = None
    resume_store: dict

class SessionResponse(BaseModel):
    session_id: str
    message: str 