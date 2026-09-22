import secrets
from fastapi import HTTPException, Header, Depends
from dependencies.auth import get_current_session

async def verify_csrf(
        csrf_token: str | None = Header(
            default=None,
            alias='X-CSRF-Token',
        ),
        session: dict = Depends(get_current_session)
):
    expected_token = session["csrf_token"]
    if csrf_token is None or not secrets.compare_digest(expected_token, csrf_token):
        raise HTTPException(
            status_code=403,
            detail="Invalid CSRF token",
        )
    return session