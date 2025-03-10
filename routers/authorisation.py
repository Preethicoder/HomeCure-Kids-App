from fastapi import APIRouter, HTTPException, status

from starlette.requests import Request
from starlette.responses import JSONResponse

from database.database import get_db_connection
from database.models import User, LoginUser
from auth import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])
# User sign up endpoint
@router.post("/signup")
def sign_up(user: User):
    """
        Endpoint for signing up a new user.
        This endpoint checks if the username is available, hashes the password,
        and stores the user credentials in the database.

        Args:
            user (User): The user object containing username and password.

        Returns:
            JSONResponse: Success message if user is created, otherwise an error message.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=%s", (user.username,))
    existing_user = cursor.fetchone()
    if existing_user:
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = hash_password(user.password)
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)",
                   (user.username, hashed_password))

    conn.commit()
    conn.close()
    return JSONResponse(status_code=201, content={"message": "User created successfully"})


# Login endpoint that creates session-based authentication
@router.post("/login")
async def login(request: Request, login_user: LoginUser):
    """
        Endpoint for logging in a user.
        This endpoint verifies the username and password, and if valid,
        stores the user information in the session for authentication.

        Args:
            request (Request): The request object containing session data.


        Returns:
            JSONResponse: Success message if login is successful,
             otherwise an error message.
             :param request:
             :param login_user:
    """
    print("request",request)
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=%s", (login_user.username,))
    db_user = cursor.fetchone()
    conn.close()

    if not db_user or not verify_password(login_user.password, db_user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password")

    # Store user information in session
    request.session["user_id"] = db_user["id"]
    request.session["username"] = db_user["username"]

    return JSONResponse(content={"message": "Login successful"})

# Endpoint to logout and clear session
@router.post("/logout")
async def logout(request: Request):
    """
        Endpoint to logout the current user by clearing the session.
        This ensures the user is logged out and their session is terminated.

        Args:
            request (Request): The request object to clear the session data.

        Returns:
            JSONResponse: Success message indicating the user has logged out.
    """
    request.session.clear()  # Clear session data
    return JSONResponse(content={"message": "Logged out successfully"})