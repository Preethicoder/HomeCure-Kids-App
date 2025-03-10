import json
import os
import re
from typing import List, Optional

import groq
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

load_dotenv()

# Configure the Groq API
client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))


# Define the structured response format using Pydantic
class RemedyInstruction(BaseModel):
    remedy_name: str
    steps: Optional[List[str]] = None  # List of strings


def clean_and_parse_response(response_text: str):
    """
    Cleans and converts API response into RemedyInstruction format.
    """
    try:
        # Remove markdown formatting if present
        response_text = re.sub(r'```json|```', '', response_text).strip()

        # Parse JSON string
        remedy_data = json.loads(response_text)

        # Convert structure if necessary
        if "remedy" in remedy_data:
            remedy_data["remedy_name"] = remedy_data.pop("remedy")

        if "steps" in remedy_data and isinstance(remedy_data["steps"], list):
            remedy_data["steps"] = [
                step if isinstance(step, str) else step.get("action", step.get("caution", ""))
                for step in remedy_data["steps"]
            ]

        # Validate and return the formatted response
        return RemedyInstruction(**remedy_data)

    except ValidationError as e:
        print(f"Error parsing remedy instructions: {e}")
        return None
    except json.JSONDecodeError:
        print("Error: Invalid JSON response from API.")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def generate_remedy_instructions(symptom: str, available_ingredients: list, allergies: list = None):
    """
    Calls Groq API to generate kitchen remedy instructions based on the given symptom and available ingredients.
    """
    filtered_ingredients = available_ingredients[:]

    if allergies:
        for allergy in allergies:
            if allergy in filtered_ingredients:
                filtered_ingredients.remove(allergy)

    try:
        chat_input = [
            {
                "role": "system",
                "content": """You are a professional medical assistant specializing in home remedies for children's common illnesses.
                              Provide short, step-by-step instructions in a structured JSON response format using ONLY the available ingredients and include no extra ingredients .
                              If any of the available ingredients require caution (such as honey for children under 1 year old), you must explicitly include a caution message in the steps, clearly noting why the ingredient should be avoided or used with care. 
                              For example: 'Caution: Honey should not be given to children under 1 year old due to the risk of botulism.'
                              Example: 
                                   - Step 1: Mix warm water with honey.
                                   - Step 2: Add lemon juice and stir well.
                                   - Step 3: Drink slowly to soothe the throat.
                                   - **Step 4 (Caution)**: Honey should not be given to children under 1 year old due to the risk of botulism.

                             Pay special attention to spices and any ingredient that can be an irritant. Always explicitly include a caution message as the **LAST step** for any ingredient that can cause throat or lung irritation. 
                             Format your response as a JSON dictionary with the following structure:
                                          {
                                            "remedy_name": "Name of the remedy",
                                             "steps": ["Step 1: Do this", "Step 2: Do that"]
                                           }
                             If no remedy is possible with the available ingredients, return the string "No remedy possible with available ingredients." and nothing else.
                             Ensure the response is valid JSON, unless no remedy is possible.
                                           """

            },
            {
                "role": "user",
                "content": f"My child has {symptom}. What home remedy can I use? I have these ingredients: {', '.join(filtered_ingredients) if filtered_ingredients else 'none'}."
            }
        ]
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=chat_input,
            max_tokens=2048,
            temperature=0,
        )

        # ✅ Extract and clean response
        remedy_data_str = response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return "Error: Groq API call failed."

    if remedy_data_str.lower() == "no remedy possible with available ingredients.":
        try:
            chat_input = [
                {
                    "role": "system",
                    "content": """You are a helpful assistant specializing in suggesting minimum grocery items for common children's symptoms.
                                  Given a symptom, provide a short list of the most essential items to purchase to create home remedies.
                                  Focus on basic, widely available ingredients.
                                  Respond in a simple, comma-separated list format.
                                  Example: "Honey, Lemon, Ginger"""
                },
                {
                    "role": "user",
                    "content": f"My child has {symptom}. What are the minimum items I should buy?"
                }
            ]
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=chat_input,
                max_tokens=512,
                temperature=0,
            )

            # ✅ Extract shopping list
            shopping_list = response.choices[0].message.content.strip()
            return shopping_list
        except Exception as e:
            print(f"Error calling Groq API for shopping list: {e}")
            return "Error: Could not generate shopping list."

    else:
        # ✅ Parse and validate response
        return clean_and_parse_response(remedy_data_str)


def main():
    symptom = "a cough"
    ingredients = ["cinnamon"]
    allergies = ["cinnamon"]

    remedy = generate_remedy_instructions(symptom, ingredients, allergies)
    print(remedy)


if __name__ == "__main__":
    main()
