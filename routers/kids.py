from fastapi import APIRouter, Depends, HTTPException, status
from database.database import get_db_connection
from database.models import KidsProfile
from utils.authuser_session import get_current_user

router = APIRouter(prefix="/kids", tags=["Kids Profile"])
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
async def update_kidsprofile(kid_id: int, kid: KidsProfile,
                             current_user: dict = Depends(get_current_user)):
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
        print(kid.allergies)
        # Check each field and add to the update query if provided
        if kid.name != "string":
            print(kid.name)
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
        if kid.allergies != "string":
            print("inside kids_allergies")
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
        return {"message": "Kids_profile updated successfully",
                "kid_id": kid_id}

    except HTTPException as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Database error occurred.") from e


