# Module Docstring:
"""
This module contains all the API endpoints related to
user management, kids' profiles, ingredients, and symptoms.
It includes user authentication (signup, login, logout),
CRUD operations for kids' profiles, ingredient management,
and symptom tracking for kids. Each endpoint ensures
secure session-based authentication for users.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from starlette.requests import Request
from starlette.responses import JSONResponse

from auth import hash_password, verify_password
from database import get_db_connection
from models import User, KidsProfile, Ingredients, KidsProfileSymptom

router = APIRouter()


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
async def login(request: Request, username: str, password: str):
    """
        Endpoint for logging in a user.
        This endpoint verifies the username and password, and if valid,
        stores the user information in the session for authentication.

        Args:
            request (Request): The request object containing session data.
            username (str): The username provided by the user.
            password (str): The password provided by the user.

        Returns:
            JSONResponse: Success message if login is successful,
             otherwise an error message.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    db_user = cursor.fetchone()
    conn.close()

    if not db_user or not verify_password(password, db_user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password")

    # Store user information in session
    request.session["user_id"] = db_user["id"]
    request.session["username"] = db_user["username"]

    return JSONResponse(content={"message": "Login successful"})


# Get current user from session
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


# Endpoint to create kids' profiles
@router.post("/add_kid_profile", status_code=status.HTTP_201_CREATED)
async def create_kids_profile(
        kids_profile: KidsProfile, current_user: dict = Depends(get_current_user)
):
    """
        Endpoint to create a kids' profile for an authenticated user.
        This endpoint stores the child's profile details and
        associates it with the authenticated parent.

        Args:
            kids_profile (KidsProfile): The profile data of the child.
            current_user (dict): The authenticated user (parent).

        Returns:
            dict: A success message along with the details of the created kids' profile.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        parent_id = current_user['id']  # Get parent_id from authenticated user
        parent_username = current_user['username']  # Get parent username

        cursor.execute("""
            INSERT INTO kids_profile (name, age, height, weight, allergies, parent_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            kids_profile.name,
            kids_profile.age,
            kids_profile.height,
            kids_profile.weight,
            kids_profile.allergies,
            parent_id,  # Use the parent_id from current_user
        ))

        new_kid_id = cursor.fetchone()['id']
        conn.commit()
        conn.close()

        # Include parent username in the response
        return {"id": new_kid_id,
                "parent_username": parent_username,
                **kids_profile.dict()}

    # Re-raise HTTPExceptions
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Database error occurred.") from e


@router.get("/get_kids_profile")
async def get_kids(current_user: dict = Depends(get_current_user)):
    """
    Endpoint to retrieve all kids' profiles
    associated with the authenticated user (parent).
    This endpoint fetches kids' profiles based on the parent's id.

    Args:
        current_user (dict): The authenticated user (parent).

    Returns:
        list: A list of kids' profiles associated with the authenticated parent.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    print("-----------", current_user['id'])
    parent_id = current_user['id']
    cursor.execute("SELECT * "
                   " FROM kids_profile WHERE parent_id = %s",
                   (parent_id,))
    kids = cursor.fetchall()
    conn.close()
    if not kids:
        raise HTTPException(status_code=404,
                            detail="No Kids found for this user")
    print(kids)
    return [
        {
            "id": kid["id"],
            "name": kid["name"],
            "age": kid["age"],
            "height": kid["height"],
            "weight": kid["weight"],
            "allergies": kid["allergies"],
            **({"symptom": kid["symptom_name"]} if kid["symptom_name"] else {})  # Add symptom only if present
        }
        for kid in kids
    ]


@router.post("/update_kid_profile/{kid_id}")
async def update_kidsprofile(kid_id: int, kid: KidsProfile, current_user: dict = Depends(get_current_user)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        parent_id = current_user["id"]
        cursor.execute("SELECT * from kids_profile where id = %s and parent_id = %s", (kid_id, parent_id))
        existing_kid = cursor.fetchone()
        if not existing_kid:
            raise HTTPException(status_code=403, detail="you are not authorised to update this kids_profile")
            # Dynamically build the update query based on provided fields
        update_fields = []
        update_values = []

        # Check each field and add to the update query if provided
        if kid.name:
            update_fields.append("name = %s")
            update_values.append(kid.name)
        if kid.age != 0:
            update_fields.append("age = %s")
            update_values.append(kid.age)
        if kid.height != 0:
            update_fields.append("height = %s")
            update_values.append(kid.height)
        if kid.weight != 0:
            update_fields.append("weight = %s")
            update_values.append(kid.weight)
        if kid.allergies:
            update_fields.append("allergies = %s")
            update_values.append(kid.allergies)

        # If there are no fields to update, raise an exception
        if not update_fields:
            raise HTTPException(status_code=400, detail="No valid fields to update.")
            # Add the condition to the query
        update_query = f"UPDATE kids_profile SET {', '.join(update_fields)} WHERE id = %s AND parent_id = %s"

        # Add the kid_id and parent_id to the values
        update_values.extend([kid_id, parent_id])

        # Execute the update query
        cursor.execute(update_query, tuple(update_values))

        # Commit the changes to the database
        conn.commit()
        conn.close()
        return {"message": "Symptom updated successfully",
                "kid_id": kid_id}

    except HTTPException as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Database error occurred.") from e


@router.post("/add_ingredient/")
async def add_ingredients(ingredients: Ingredients, current_user: dict = Depends(get_current_user)):
    """
        Endpoint to add ingredients to the
        authenticated user's ingredient list.
        This endpoint allows the parent to add
        ingredients with their availability status.

        Args:
            ingredients (Ingredients): The ingredient details to be added.
            current_user (dict): The authenticated user (parent).

        Returns:
            JSONResponse: Success message
            if ingredients are added, otherwise an error message.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        parent_id = current_user["id"]
        cursor.execute("""
            INSERT INTO ingredients(ingredient_name,is_available,parent_id)
            VALUES (%s, %s ,%s)
        """, (
            ingredients.ingredient_name,
            ingredients.is_available,
            parent_id
        ))
        conn.commit()
        conn.close()
        return JSONResponse(status_code=201,
                            content={"message": "Ingredients added successfull"})
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Database error occurred.") from e


@router.get("/get_ingredient/")
async def get_ingredients(current_user: dict = Depends(get_current_user)):
    """
        Endpoint to add ingredients to the authenticated user's ingredient list.
        This endpoint allows the parent to add ingredients with their availability status.

        Args:
            ingredients (Ingredients): The ingredient details to be added.
            current_user (dict): The authenticated user (parent).

        Returns:
            JSONResponse: Success message if ingredients are added, otherwise an error message.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    parent_id = current_user["id"]
    cursor.execute("""
        SELECT * from ingredients where parent_id = %s
        """, (parent_id,))
    ingredients = cursor.fetchall()
    if not ingredients:
        raise HTTPException(status_code=404,
                            detail="No Ingredients found for this user")
    return [{"ingredients_name": ingredient["ingredient_name"],
             "is_available": ingredient["is_available"]} for
            ingredient in ingredients]


@router.put("/update_ingredient/")
async def update_ingredients(ingredients: Ingredients,
                             current_user: dict = Depends(get_current_user)):
    """
        Endpoint to update the availability status of an
        ingredient for a specific user.
        This endpoint checks if the ingredient exists
        in the database for the authenticated user
        and updates its availability status accordingly.

        Args:
            ingredients (Ingredients): The ingredient details to update,
            including the ingredient name and new availability status.
            current_user (dict): The authenticated user (parent).

        Returns:
            dict: A success message containing the updated ingredient name
            and availability status if the update is successful.

        Raises:
            HTTPException:
                - 404 if the ingredient does not exist for the user.
                - 500 if there is a database error during the update process.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:

        parent_id = current_user["id"]
        # Check if ingredient exists for this user
        cursor.execute(
            "SELECT id FROM ingredients WHERE ingredient_name = %s AND parent_id = %s",
            (ingredients.ingredient_name, parent_id),
        )
        existing_ingredient = cursor.fetchone()

        if not existing_ingredient:
            raise HTTPException(status_code=404, detail="Ingredient not found for this user")

        # Update is_available status
        cursor.execute("""
        UPDATE ingredients SET is_available = %s
        where ingredient_name = %s and parent_id = %s
        """, (
            ingredients.is_available,
            ingredients.ingredient_name,
            parent_id
        ))
        conn.commit()

        return {"message": "Ingredient updated successfully",
                "ingredient": ingredients.ingredient_name,
                "is_available": ingredients.is_available}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Database error occurred.") from e
    finally:
        conn.close()


@router.post("/update_kid_symptom/{kid_id}")
async def update_kid_symptom(kid_id: int, symptom: KidsProfileSymptom,
                             current_user: dict = Depends(get_current_user)):
    """
        Endpoint to update the symptom name for a specific kid's profile.
        This endpoint ensures that only the parent (authenticated user)
        can update their child's symptom.

        Args:
            kid_id (int): The ID of the child whose symptom needs to be updated.
            symptom (KidsProfileSymptom): The new symptom information to update.
            current_user (dict): The authenticated user (parent).

        Returns:
            dict: Success message with updated symptom details.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        parent_id = current_user["id"]

        cursor.execute("SELECT * FROM kids_profile where id = %s and parent_id= %s",
                       (kid_id, parent_id))
        existing_kid = cursor.fetchone()
        if not existing_kid:
            raise HTTPException(status_code=403,
                                detail="you are not authorised to update this kid's symptoms")
        cursor.execute("""UPDATE kids_profile SET symptom_name = %s WHERE id = %s
        """, (symptom.symptom_name, kid_id))
        conn.commit()
        conn.close()

        return {"message": "Symptom updated successfully",
                "kid_id": kid_id, "symptom_name": symptom.symptom_name}
    except Exception as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500,
                            detail="Database error occurred") from e


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


# Home endpoint
@router.get("/")
def home():
    """
        Home endpoint that returns a welcome message.

        Returns:
            dict: A simple welcome message.
        """
    return {"message": "Welcome to the Home Remedy App for Kids"}
