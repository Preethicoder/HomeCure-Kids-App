from fastapi import APIRouter, Depends, HTTPException
from matplotlib.backend_bases import cursors

from database.database import get_db_connection
from ai_clients import gemini_client, groq_client
from database.database import get_db_connection
from ai_clients.openai_client import generate_remedy_instructions

import json

from routes import get_current_user

router = APIRouter(prefix="/remedy_shopping_list",tags=["Remedy_Shopping_List"])

@router.get("/get_shopping_list")
def get_shopping_list(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        search_query = """
               SELECT kid_id, symptom, ingredients_to_buy
               FROM remedy_shopping_list
               WHERE parent_id = %s
           """
        cursor.execute(search_query, (current_user["id"],))  # Correct parameter passing
        shopping_lists = cursor.fetchall()  # Fetch all rows
        print(shopping_lists)
        for row in shopping_lists:
            kid_id = row['kid_id']
            symptom = row['symptom']
            ingredients = row['ingredients_to_buy']
            print(f"Kid ID: {kid_id}, Symptom: {symptom}, Ingredients: {ingredients}")
            # Convert the data into a formatted list of strings
        formatted_results = [
                f"Kid ID: {row['kid_id']}, Symptom: {row['symptom']}, Ingredients: {row['ingredients_to_buy']}"
                for row in shopping_lists
            ]

        return {"shopping_lists": formatted_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()