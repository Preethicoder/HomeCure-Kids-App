# Module Docstring: This module defines Pydantic models for users and kids profiles.
"""
This module contains the Pydantic models used for handling user and kids profile data.
It includes validation for user credentials, kids' health profiles, and ingredients availability.
"""
from typing import Optional
from pydantic import BaseModel
from pydantic import Field

class User(BaseModel):
    """
        Model for User credentials.
        This model represents the data structure
        for a user in the system, including username and password.
    """
    username: str
    password: str

class LoginUser(BaseModel):
    """
        Model for Login credentials.
        This model represents the data structure used for user login,
        including username and password.
    """
    username: str
    password: str

class KidsProfile(BaseModel):
    """
        Model for Kids Profile.
        This model represents the health and personal profile of a child,
        including name, age, height, weight, and allergies.
    """
    name:str = Field(..., title="Child's Name", description="Full name of the child")  # Required
    age: int
    height: Optional[float] = None
    weight: Optional[float] = None
    allergies: Optional[str] = None

# Separate model for updating symptom_name only
class KidsProfileSymptom(BaseModel):
    """
        Model for Kids Profile Symptom.
        This model represents the symptom of a child in the system,
        used for health tracking or diagnosis.
    """
    symptom_name: str

class Ingredients(BaseModel):
    """
        Model for Ingredients availability.
        This model represents the availability of ingredients in the system,
        including the name and availability status.
    """
    ingredient_name: str
    is_available :bool


