from service.session import get_session
from fastapi import Cookie, HTTPException

async def get_current_session(
        session_id: str | None = Cookie(default=None)
):
    if session_id is None:
        raise HTTPException(status_code=404,
                            detail="Not Authenticated")
    session = await get_session(session_id)
    if session is None:
        raise HTTPException(status_code=401,
                            detail="Session expired")
    return session