from fastapi import status
from starlette.responses import JSONResponse
from fastapi import APIRouter, Depends, HTTPException
from database.database import get_db_connection
from database.models import Ingredients
from utils.authuser_session import get_current_user

router = APIRouter(prefix="/ingredients", tags=["Ingredients"])
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
            current_use r (dict): The authenticated user (parent).

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


