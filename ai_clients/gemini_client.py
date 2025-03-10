import json
import os
from typing import List, Optional

import google.generativeai as genai
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv

load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Specify the model to use
model = genai.GenerativeModel('gemini-1.5-flash')


def generate_remedy_instructions(symptom: str, available_ingredients: list, allergies: list = None):
    """
    Calls Gemini API to generate kitchen remedy instructions based on the given symptom and available ingredients.

    Args:
        symptom (str): The symptom to find a remedy for.
        available_ingredients (list): A list of available ingredients.

    Returns:
        RemedyInstruction: AI-generated remedy instructions in structured format.
    """

    # Define the structured response format using Pydantic
    class RemedyInstruction(BaseModel):
            remedy_name: str
            steps:Optional[List[str]] = None #make it optional



    filtered_ingredients = available_ingredients[:]  # Create a copy

    if allergies:
        for allergy in allergies:
            if allergy in filtered_ingredients:
                filtered_ingredients.remove(allergy)
    try:
        response = model.generate_content(
            f"""You are a professional medical assistant specializing in home remedies for children's common illnesses.
                                      Provide short, step-by-step instructions in a structured JSON response format using ONLY the available ingredients and include no extra ingredients .
                                      If any of the available ingredients require caution (such as honey for children under 1 year old), you must explicitly include a caution message in the steps, clearly noting why the ingredient should be avoided or used with care. 
                                      For example: 'Caution: Honey should not be given to children under 1 year old due to the risk of botulism.'
                                      Example: 
                      - Step 1: Mix warm water with honey.
                      - Step 2: Add lemon juice and stir well.
                      - Step 3: Drink slowly to soothe the throat.
                      - **Step 4 (Caution)**: Honey should not be given to children under 1 year old due to the risk of botulism.

                      Pay special attention to spices and any ingredient that can be an irritant. Always explicitly include a caution message as the **LAST step** for any ingredient that can cause throat or lung irritation.
                                      Pay special attention to spices, and any ingredient that can be an irritant. Always  explicitly include a caution message as the  step  for any ingredient that can cause irritations to the throat, or lungs of a child .
                                      If no remedy can be made with the remaining ingredients, state 'No remedy possible with available ingredients.'
                                      Format your response as a JSON dictionary with the following structure:
                                          {json.dumps(RemedyInstruction.model_json_schema(), indent=2)}
                                           If no remedy is possible with the available ingredients, return the string "No remedy possible with available ingredients." and nothing else.
                                           Ensure the response is valid JSON, unless no remedy is possible.

                                           My child has {symptom}. What home remedy can I use? I have these ingredients: {', '.join(filtered_ingredients) if filtered_ingredients else 'none'}."""
        )

        remedy_data_str = response.text.strip()

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Error: Gemini API call failed."

    if "No remedy possible with available ingredients." in remedy_data_str:
        try:
            response = model.generate_content(
                f"""You are a helpful assistant specializing in suggesting minimum grocery items for common children's symptoms.
                                              Given a symptom, provide a short list of the most essential items to purchase to create home remedies.
                                              Focus on basic, widely available ingredients.
                                              Respond in a simple, comma-separated list format.
                                              Example: "Honey, Lemon, Ginger"

                                              My child has {symptom}. What are the minimum items I should buy?"""
            )

            shopping_list = response.text.strip()
            print(shopping_list)
            return shopping_list

        except Exception as e:
            print(f"Error calling Gemini API for shopping list: {e}")
            return "Error: Could not generate shopping list."
    else:
        try:

                remedy_data_str = response.text.strip()
                # Clean the response by removing markdown backticks
                if remedy_data_str.startswith("```json"):
                    remedy_data_str = remedy_data_str[7:]  # Remove ```json
                if remedy_data_str.endswith("```"):
                    remedy_data_str = remedy_data_str[:-3]  # Remove ```

                remedy_data = RemedyInstruction.model_validate_json(remedy_data_str)
                print(f"Remedy Name: {remedy_data.remedy_name}")
                print(f"Remedy_Steps::", remedy_data.steps)
                return remedy_data


        except ValidationError as e:
            print(f"Error parsing remedy instructions: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None



def main():
    # Example usage
    symptom = "a cough"
    ingredients = [""]
    allergies = [""]
    remedy = generate_remedy_instructions(symptom, ingredients, allergies)



if __name__ == "__main__":
    main()