from fastapi import APIRouter, Depends, HTTPException
from database.database import get_db_connection
from database.models import KidsProfileSymptom
from utils.authuser_session import get_current_user

router = APIRouter(prefix="/symptoms", tags=["Symptoms"])
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
