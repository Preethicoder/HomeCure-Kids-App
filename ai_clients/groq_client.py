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



def generate_remedy_instructions(symptom: str, available_ingredients: list, allergies: list = None):
    """
    Calls Groq API to generate kitchen remedy instructions based on the given symptom and available ingredients.
    """
    filtered_ingredients = available_ingredients[:]
    COST_PER_1000_INPUT_TOKENS = 0.59 / 1000  # $0.59 per million input tokens
    COST_PER_1000_OUTPUT_TOKENS = 0.79 / 1000  # $0.79 per million output tokens
    remedy_data_str = ""
    if allergies:
        for allergy in allergies:
            if allergy in filtered_ingredients:
                filtered_ingredients.remove(allergy)
    if filtered_ingredients:
      try:
        chat_input = [
            {
                    "role": "system",
                    "content": f"""You are a professional medical assistant specializing in home remedies for children's common illnesses.
                Provide short, step-by-step instructions in a structured JSON response format using ONLY the available ingredients and include no extra ingredients .
                If any of the available ingredients require caution (such as honey for children under 1 year old), you must explicitly include a caution message in the steps, clearly noting why the ingredient should be avoided or used with care. 
                For example:      For example:  ### **Common Caution Triggers**:
              - **Garlic, Onion, Ginger, Chili, Black Pepper** → May cause skin irritation or burns. Always test on a small patch of skin first.  
              - **Lemon, Vinegar** → Can sting and increase sun sensitivity. Dilute before use.  
              - **Tea Tree Oil, Peppermint Oil, Clove Oil** → Strong essential oils can irritate the skin if undiluted.  
              - **Honey** → Do **not** give to infants under 1 year old due to botulism risk.  
              - **Raw Egg** → Risk of bacterial infection; avoid on open wounds.  
                Example: 
                      - Step 1: Mix warm water with honey.
                      - Step 2: Add lemon juice and stir well.
                      - Step 3: Drink slowly to soothe the throat.
                      - **Step 4 (Caution)**: Honey should not be given to children under 1 year old due to the risk of botulism.

                Pay special attention to spices and any ingredient that can be an irritant. Always explicitly include a caution message as the **LAST step** for any ingredient that can cause throat or lung irritation.
                 Format your response as a JSON dictionary with the following structure:
                        {json.dumps(RemedyInstruction.model_json_schema(), indent=2)}
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
            model="llama-3.3-70b-versatile",#llama-3.3-70b-versatile llama3-8b-8192
            messages=chat_input,
            max_tokens=256,
            temperature=0.3
        )

        # ✅ Extract and clean response
        remedy_data_str = response.choices[0].message.content.strip()
        total_tokens = response.usage.total_tokens
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        print(f"Total tokens used: {total_tokens}")
        print(f"Tokens used for the prompt: {prompt_tokens}")
        print(f"Tokens used for the completion: {completion_tokens}")

        input_cost = (prompt_tokens / 1000) * COST_PER_1000_INPUT_TOKENS
        output_cost = (completion_tokens / 1000) * COST_PER_1000_OUTPUT_TOKENS
        total_cost = input_cost + output_cost
        # Print the cost breakdown
        print(f"Prompt Tokens Cost: ${input_cost:.6f}")
        print(f"Completion Tokens Cost: ${output_cost:.6f}")
        print(f"Total Cost: ${total_cost:.6f}")
        print(remedy_data_str)

      except Exception as e:
        print(f"Error calling Groq API: {e}")
        return "Error: Groq API call failed."

    if remedy_data_str.lower() == "no remedy possible with available ingredients." or not filtered_ingredients:
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
                model="llama-3.3-70b-versatile",#llama-3.3-70b-versatile llama3-8b-8192 Allam-2-7b
                messages=chat_input,
                max_tokens=256,
                temperature=0.3
            )

            # ✅ Extract shopping list
            shopping_list = response.choices[0].message.content.strip()
            total_tokens = response.usage.total_tokens
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            print(f"Total tokens used: {total_tokens}")
            print(f"Tokens used for the prompt: {prompt_tokens}")
            print(f"Tokens used for the completion: {completion_tokens}")


            input_cost = (prompt_tokens / 1000) * COST_PER_1000_INPUT_TOKENS
            output_cost = (completion_tokens / 1000) * COST_PER_1000_OUTPUT_TOKENS
            total_cost = input_cost + output_cost
            # Print the cost breakdown
            print(f"Prompt Tokens Cost: ${input_cost:.6f}")
            print(f"Completion Tokens Cost: ${output_cost:.6f}")
            print(f"Total Cost: ${total_cost:.6f}")
            return shopping_list
        except Exception as e:
            print(f"Error calling Groq API for shopping list: {e}")
            return "Error: Could not generate shopping list."


        # ✅ Parse and validate response
       # return clean_and_parse_response(remedy_data_str)
    print(remedy_data_str)
    remedy_data_str = re.sub(r'```json|```', '', remedy_data_str).strip()
    # Extract token usage from response

    return RemedyInstruction.model_validate_json(remedy_data_str)



def main():
    symptom = "Ear Pain"
    ingredients = ["parupu"]
    allergies = []

    remedy = generate_remedy_instructions(symptom, ingredients, allergies)
    print("remedy",remedy)


if __name__ == "__main__":
    main()