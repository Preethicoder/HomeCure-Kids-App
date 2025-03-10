from fastapi import APIRouter, Depends, HTTPException

from ai_clients import gemini_client, groq_client
from database.database import get_db_connection
from ai_clients.openai_client import generate_remedy_instructions
from utils.authuser_session import get_current_user
import json
router = APIRouter(prefix="/remedies", tags=["Kitchen_Remedy"])
def get_existing_remedy(symptom_name,ingredients):
    try:
        conn= get_db_connection()
        cursor = conn.cursor()
        search_query = """
             SELECT remedy_name, steps, symptom, ingredients
             FROM remedies
             WHERE symptom = %s
             AND 
             (SELECT array_agg(value ORDER BY value) FROM jsonb_array_elements_text(ingredients::jsonb)) = 
             (SELECT array_agg(value ORDER BY value) FROM jsonb_array_elements_text(%s::jsonb))
              LIMIT 1;
              """
        cursor.execute(search_query, (symptom_name, json.dumps(sorted(ingredients))))
        result = cursor.fetchone()
        if result:
            return result
        return None
    except Exception as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500,
                            detail="Database error occurred") from e
# Home endpoint

@router.get("/get_kitchen_remedy/open_ai/{kid_id}")
async def get_remedy(kid_id: int, current_user: dict = Depends(get_current_user)):
    """
        Retrieves the symptom for a given kid and suggests ingredients based on the symptom.

        Args:
            kid_id (int): The ID of the child whose symptom needs to be retrieved.
            current_user (dict): The currently authenticated parent user, fetched using dependency injection.

        Returns:
            dict: A JSON object containing the kid's ID, symptom, and a list of suggested ingredients.

        Raises:
            HTTPException 403: If the user is not authorized to access the kid's profile.
            HTTPException 404: If no symptom is found for the given kid.
            HTTPException 500: If there is an internal server error.

        Example Response:
            {
                "kid_id": 1,
                "symptom": "Cough",
                "ingredients": ["Honey", "Ginger", "Lemon"]
            }
        """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:

        parent_id = current_user["id"]
        cursor.execute("SELECT symptom_name FROM kids_profile WHERE id = %s and parent_id = %s", (kid_id, parent_id))
        kid_symptom = cursor.fetchone()

        symptom = kid_symptom["symptom_name"]
        print(f"symptom::{symptom}")

        # Fetch ingredients based on the symptom
        cursor.execute("SELECT ingredient_name "
                       "FROM ingredients WHERE is_available = true "
                       "and parent_id = %s",
                       (parent_id,))
        ingredients = cursor.fetchall()
        ingredients_list = [
            ingredient["ingredient_name"] for ingredient in ingredients]  # Extract ingredients as a list

        print("Remedy Information:")
        print(f"  Kid ID: {kid_id}")
        print(f"  Symptom: {symptom}")
        print(f"  Ingredients: {ingredients_list}")

        result = get_existing_remedy(symptom,ingredients_list)

        if result:
            print(f"result:{result}")
            print(f"result[0]::{result['remedy_name']}")
            print(f"result[1]::{result['steps']}")
            insert_query = """
                                        INSERT INTO remedies (kid_id, parent_id, symptom, remedy_name, steps, ingredients)
                                        VALUES (%s, %s, %s, %s, %s, %s)
                                    """
            cursor.execute(insert_query, (
                kid_id,
                parent_id,
                symptom,
                result['remedy_name'],
                json.dumps(result['steps']),
                json.dumps(ingredients_list)
            ))
            conn.commit()
            remedy_instructions= {
            "kid_id": kid_id,
            "symptom": symptom,
            "ingredients": ingredients_list,
         "remedy_name": result["remedy_name"],
           "steps": result["steps"]
    }
            return remedy_instructions
        else:
            # Generate AI remedy instructions
            remedy_instructions = generate_remedy_instructions(symptom, ingredients_list)
            print("remedy_instructions",remedy_instructions)
            ##remedy_instructions = remedy_instructions.replace("\n", " ")
        if hasattr(remedy_instructions, 'remedy_name') and hasattr(remedy_instructions,
                                                                   'steps'):  # check if remedy instruction is a pydantic object
                print(f"   inside Remedy Name: {remedy_instructions.remedy_name}")
                print(f"    Steps:{remedy_instructions.steps}")
                insert_query = """
                                INSERT INTO remedies (kid_id, parent_id, symptom, remedy_name, steps, ingredients)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """
                cursor.execute(insert_query,(
                             kid_id,
                             parent_id,
                             symptom,
                             remedy_instructions.remedy_name,
                             json.dumps(remedy_instructions.steps),
                            json.dumps(ingredients_list)
                             ))
                conn.commit()
                print("returned::::",remedy_instructions)

                return {
            "kid_id": kid_id,
            "symptom": symptom,
            "ingredients": ingredients_list,
            "remedy_instructions": remedy_instructions

        }
        else:
            if isinstance(remedy_instructions, str):
                return {
                    "kid_id": kid_id,
                    "symptom": symptom,
                    "Ingreidents_to_Buy": remedy_instructions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
@router.get("/get_kitchen_remedy/gemini_client/{kid_id}")
async def get_remedy(kid_id: int, current_user: dict = Depends(get_current_user)):
    """
        Retrieves the symptom for a given kid and suggests ingredients based on the symptom.

        Args:
            kid_id (int): The ID of the child whose symptom needs to be retrieved.
            current_user (dict): The currently authenticated parent user, fetched using dependency injection.

        Returns:
            dict: A JSON object containing the kid's ID, symptom, and a list of suggested ingredients.

        Raises:
            HTTPException 403: If the user is not authorized to access the kid's profile.
            HTTPException 404: If no symptom is found for the given kid.
            HTTPException 500: If there is an internal server error.

        Example Response:
            {
                "kid_id": 1,
                "symptom": "Cough",
                "ingredients": ["Honey", "Ginger", "Lemon"]
            }
        """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:

        parent_id = current_user["id"]
        cursor.execute("SELECT symptom_name FROM kids_profile WHERE id = %s and parent_id = %s", (kid_id, parent_id))
        kid_symptom = cursor.fetchone()

        symptom = kid_symptom["symptom_name"]
        print(f"symptom::{symptom}")

        # Fetch ingredients based on the symptom
        cursor.execute("SELECT ingredient_name "
                       "FROM ingredients WHERE is_available = true "
                       "and parent_id = %s",
                       (parent_id,))
        ingredients = cursor.fetchall()
        ingredients_list = [
            ingredient["ingredient_name"] for ingredient in ingredients]  # Extract ingredients as a list

        print("Remedy Information:")
        print(f"  Kid ID: {kid_id}")
        print(f"  Symptom: {symptom}")
        print(f"  Ingredients: {ingredients_list}")
        remedy_instructions = gemini_client.generate_remedy_instructions(symptom, ingredients_list)
        print("remedy_instructions",remedy_instructions)
            ##remedy_instructions = remedy_instructions.replace("\n", " ")
        if hasattr(remedy_instructions, 'remedy_name') and hasattr(remedy_instructions,
                                                                   'steps'):  # check if remedy instruction is a pydantic object
                print(f"   inside Remedy Name: {remedy_instructions.remedy_name}")
                print(f"    Steps:{remedy_instructions.steps}")

                print("returned::::",remedy_instructions)

                return {
            "kid_id": kid_id,
            "symptom": symptom,
            "ingredients": ingredients_list,
            "remedy_instructions": remedy_instructions

        }
        else:
            if isinstance(remedy_instructions, str):
                return {
                    "kid_id": kid_id,
                    "symptom": symptom,
                    "Ingreidents_to_Buy": remedy_instructions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.get("/get_kitchen_remedy/groq_client/{kid_id}")
async def get_remedy(kid_id: int, current_user: dict = Depends(get_current_user)):
    """
            Retrieves the symptom for a given kid and suggests ingredients based on the symptom.

            Args:
                kid_id (int): The ID of the child whose symptom needs to be retrieved.
                current_user (dict): The currently authenticated parent user, fetched using dependency injection.

            Returns:
                dict: A JSON object containing the kid's ID, symptom, and a list of suggested ingredients.

            Raises:
                HTTPException 403: If the user is not authorized to access the kid's profile.
                HTTPException 404: If no symptom is found for the given kid.
                HTTPException 500: If there is an internal server error.

            Example Response:
                {
                    "kid_id": 1,
                    "symptom": "Cough",
                    "ingredients": ["Honey", "Ginger", "Lemon"]
                }
            """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:

        parent_id = current_user["id"]
        cursor.execute("SELECT symptom_name FROM kids_profile WHERE id = %s and parent_id = %s", (kid_id, parent_id))
        kid_symptom = cursor.fetchone()

        symptom = kid_symptom["symptom_name"]
        print(f"symptom::{symptom}")

        # Fetch ingredients based on the symptom
        cursor.execute("SELECT ingredient_name "
                       "FROM ingredients WHERE is_available = true "
                       "and parent_id = %s",
                       (parent_id,))
        ingredients = cursor.fetchall()
        ingredients_list = [
            ingredient["ingredient_name"] for ingredient in ingredients]  # Extract ingredients as a list

        print("Remedy Information:")
        print(f"  Kid ID: {kid_id}")
        print(f"  Symptom: {symptom}")
        print(f"  Ingredients: {ingredients_list}")
        remedy_instructions = groq_client.generate_remedy_instructions(symptom, ingredients_list)
        print("remedy_instructions", remedy_instructions)
        ##remedy_instructions = remedy_instructions.replace("\n", " ")
        if hasattr(remedy_instructions, 'remedy_name') and hasattr(remedy_instructions,
                                                                   'steps'):  # check if remedy instruction is a pydantic object
            print(f"   inside Remedy Name: {remedy_instructions.remedy_name}")
            print(f"    Steps:{remedy_instructions.steps}")

            print("returned::::", remedy_instructions)

            return {
                "kid_id": kid_id,
                "symptom": symptom,
                "ingredients": ingredients_list,
                "remedy_instructions": remedy_instructions

            }
        else:
            if isinstance(remedy_instructions, str):
                return {
                    "kid_id": kid_id,
                    "symptom": symptom,
                    "Ingreidents_to_Buy": remedy_instructions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
