# Get current user from session
from http.client import HTTPException
from fastapi import APIRouter, Depends, HTTPException, status
from starlette.requests import Request


async def get_current_user(request: Request):
    """
        Helper function to retrieve the currently authenticated user from the session.

        Args:
            request (Request): The request object containing session data.

        Returns:
            dict: The user data (id and username) if authenticated,
             otherwise raises HTTP 401 Unauthorized.
    """
    user_id = request.session.get("user_id")
    username = request.session.get("username")

    if not user_id or not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User not logged in")

    return {"id": user_id, "username": username}
