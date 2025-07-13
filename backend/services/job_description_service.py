from fastapi import HTTPException
from ..managers.session_manager import session_manager
from fastapi.responses import JSONResponse
from ..models.schemas import SessionResponse
from ..helpers.response_utils import create_session_response

def handle_job_description(job_description, session_id: str = None):
    trimmed_job_description = job_description.description.strip()
    if not trimmed_job_description:
        raise HTTPException(
            status_code=400,
            detail="Job description cannot be empty"
        )
    
    # Check job description length (max 10,000 characters)
    if len(trimmed_job_description) > 10000:
        raise HTTPException(
            status_code=400,
            detail="Job description is too long. Maximum allowed is 10,000 characters"
        )
    if not session_id or not session_manager.is_valid_session(session_id):
        session_id = session_manager.create_session()
    if not session_manager.update_job_description(session_id, trimmed_job_description):
        raise HTTPException(
            status_code=500,
            detail="Failed to store job description"
        )
    return create_session_response(
        session_id=session_id,
        message="Job description stored successfully"
    ) 