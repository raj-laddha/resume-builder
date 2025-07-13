from fastapi.responses import JSONResponse
from ..models.schemas import SessionResponse
import os

# Determine if we're in production environment
environment = os.getenv('ENVIRONMENT', 'development')
is_production = environment.lower() == 'production'

def create_session_response(session_id: str, message: str) -> JSONResponse:
    response = JSONResponse(
        content=SessionResponse(
            session_id=session_id,
            message=message
        ).model_dump()
    )
    
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=is_production,  # True in production, False in development
        samesite="lax",
        max_age=int(os.getenv('SESSION_COOKIE_MAX_AGE', 1800))
    )
    return response 