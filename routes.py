from fastapi import APIRouter, Depends, HTTPException, status
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.middleware.sessions import SessionMiddleware
from datetime import timedelta, datetime
from database import get_db_connection, init_db

from models import User, KidsProfile, Ingredients, KidsProfileSymptom
from auth import hash_password, verify_password

router = APIRouter()




# User sign up endpoint
@router.post("/signup")
def sign_up(user: User):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=%s", (user.username,))
    existing_user = cursor.fetchone()
    if existing_user:
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = hash_password(user.password)
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (user.username, hashed_password))

    conn.commit()
    conn.close()
    return JSONResponse(status_code=201, content={"message": "User created successfully"})

# Login endpoint that creates session-based authentication
@router.post("/login")
async def login(request: Request, username: str, password: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    db_user = cursor.fetchone()
    conn.close()

    if not db_user or not verify_password(password, db_user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    # Store user information in session
    request.session["user_id"] = db_user["id"]
    request.session["username"] = db_user["username"]

    return JSONResponse(content={"message": "Login successful"})

# Get current user from session
async def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    username = request.session.get("username")

    if not user_id or not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not logged in")

    return {"id": user_id, "username": username}

# Endpoint to create kids' profiles
@router.post("/kids_profile", status_code=status.HTTP_201_CREATED)
async def create_kids_profile(
    kids_profile: KidsProfile, current_user: dict = Depends(get_current_user)
):
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
        return {"id": new_kid_id, "parent_username": parent_username, **kids_profile.dict()}

    except HTTPException as e:
        raise  # Re-raise HTTPExceptions
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred.")





@router.get("/getkids")
async def get_kids(current_user:dict=Depends(get_current_user)):
        conn = get_db_connection()
        cursor = conn.cursor()
        print("-----------",current_user['id'])
        parent_id = current_user['id']
        cursor.execute("SELECT id,name ,age,height,weight,allergies  FROM kids_profile WHERE parent_id = %s",
                       (parent_id,))
        kids = cursor.fetchall()
        conn.close()
        if not kids:
            raise HTTPException(status_code=404,detail="No Kids found for this user")
        return [{"id": kid["id"], "name": kid["name"], "age": kid["age"],
                 "height": kid["height"], "weight": kid["weight"], "allergies": kid["allergies"]}
                for kid in kids]


@router.post("/add_ingredient/")
async def add_ingredients(ingredients:Ingredients,current_user:dict=Depends(get_current_user)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        parent_id = current_user["id"]
        cursor.execute("""
            INSERT INTO ingredients(ingredient_name,is_available,parent_id)
            VALUES (%s, %s ,%s)
        """,(
            ingredients.ingredient_name,
            ingredients.is_available,
            parent_id
        ))
        conn.commit()
        conn.close()
        return JSONResponse(status_code=201,content={"message":"Ingredients added successfull"})
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred.")

@router.post("/update_kid_symptom/{kid_id}")
async def update_kid_symptom(kid_id: int, symptom: KidsProfileSymptom, current_user: dict = Depends(get_current_user)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        parent_id = current_user["id"]

        cursor.execute("SELECT * FROM kids_profile where id = %s and parent_id= %s",(kid_id,parent_id))
        existing_kid = cursor.fetchone()
        if not existing_kid:
            raise HTTPException(status_code=403,detail="you are not authorised to update this kid's symptoms")
        cursor.execute("""UPDATE kids_profile SET symptom_name = %s WHERE id = %s
        """,(symptom.symptom_name,kid_id))
        conn.commit()
        conn.close()

        return {"message": "Symptom updated successfully", "kid_id": kid_id, "symptom_name": symptom.symptom_name}
    except Exception as e:
           print(f"Database error: {e}")
           raise HTTPException(status_code=500, detail="Database error occurred")
@router.get("/get_ingredient/")
async  def get_ingredients(current_user:dict=Depends(get_current_user)):
    conn = get_db_connection()
    cursor =conn.cursor()
    parent_id = current_user["id"]
    cursor.execute("""
        SELECT * from ingredients where parent_id = %s
        """,(parent_id,))
    ingredients = cursor.fetchall()
    if not ingredients:
        raise HTTPException(status_code=404,detail="No Ingredients found for this user")
    return [ {"ingredients_name":ingredient["ingredient_name"],"is_available":ingredient["is_available"]}for ingredient in ingredients]
@router.put("/update_ingredient/")
async def update_ingredients(ingredients:Ingredients,current_user:dict=Depends(get_current_user)):
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
        """,(
            ingredients.is_available,
            ingredients.ingredient_name,
            parent_id
        ))
        conn.commit()

        return {"message": "Ingredient updated successfully", "ingredient": ingredients.ingredient_name,
                "is_available": ingredients.is_available}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred.")
    finally:
        conn.close()
# Endpoint to logout and clear session
@router.post("/logout")
async def logout(request: Request):
    request.session.clear()  # Clear session data
    return JSONResponse(content={"message": "Logged out successfully"})

# Home endpoint
@router.get("/")
def home():
    return {"message": "Welcome to the home page"}
