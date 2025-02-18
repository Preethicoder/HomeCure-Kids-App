from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    username: str
    password: str

class LoginUser(BaseModel):
    username: str
    password: str

class KidsProfile(BaseModel):
    name: str
    age: int
    height: Optional[float] = None
    weight: Optional[float] = None
    allergies: Optional[str] = None

# Separate model for updating symptom_name only
class KidsProfileSymptom(BaseModel):
    symptom_name: str

class Ingredients(BaseModel):
    ingredient_name: str
    is_available :bool

