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
COST_PER_1000_INPUT_TOKENS = 0.075 / 1000
COST_PER_1000_OUTPUT_TOKENS = 0.30 / 1000

def generate_remedy_instructions(symptom: str, available_ingredients: list,allergies : list, temperature: float = 0.5, max_output_tokens: int = 500):
    """
    Calls Gemini API to generate kitchen remedy instructions based on the given symptom and available ingredients.

    Args:
        symptom (str): The symptom to find a remedy for.
        available_ingredients (list): A list of available ingredients.
        allergies (list): list of allergies
        temperature (float): Controls randomness of output.
        max_output_tokens (int): Limits the number of tokens in the response.

    Returns:
        RemedyInstruction: AI-generated remedy instructions in structured format.
    """

    # Define the structured response format using Pydantic
    class RemedyInstruction(BaseModel):
        remedy_name: str
        steps: Optional[List[str]] = None  # make it optional

    filtered_ingredients = [ingredient for ingredient in available_ingredients if ingredient not in (allergies or [])]
    remedy_data_str = ""
    response = ""

    user_prompt = f"My child has {symptom}. What home remedy can I use? I have these ingredients: {', '.join(filtered_ingredients) if filtered_ingredients else 'none'}."
    model_prompt = f"""You are a professional medical assistant specializing in home remedies for children's common illnesses.
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
                 for example:
                        {json.dumps(RemedyInstruction.model_json_schema(), indent=2)}
                If no remedy is possible with the available ingredients, return the string "No remedy possible with available ingredients." and nothing else.
                Ensure the response is valid JSON, unless no remedy is possible."""
    if filtered_ingredients:
       try:
        response = model.generate_content(
            [model_prompt, user_prompt],
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            ),
        )

        remedy_data_str = response.text.strip()
        #print(remedy_data_str)
        # Calculate and print costs
        total_tokens = response.usage_metadata.total_token_count
        prompt_tokens = response.usage_metadata.prompt_token_count
        completion_tokens = response.usage_metadata.candidates_token_count

        input_cost = (prompt_tokens / 1000) * COST_PER_1000_INPUT_TOKENS
        output_cost = (completion_tokens / 1000) * COST_PER_1000_OUTPUT_TOKENS
        total_cost = input_cost + output_cost

        print(f"Total tokens used: {total_tokens}")
        print(f"Tokens used for the prompt: {prompt_tokens}")
        print(f"Tokens used for the completion: {completion_tokens}")
        print(f"Prompt Tokens Cost: ${input_cost:.6f}")
        print(f"Completion Tokens Cost: ${output_cost:.6f}")
        print(f"Total Cost: ${total_cost:.6f}")

       except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Error: Gemini API call failed."

    if "No remedy possible with available ingredients." in remedy_data_str or not filtered_ingredients:

        try:
            user_prompt_shop = f"My child has {symptom}. What are the minimum items I should buy?"
            model_prompt_shop = """You are a helpful assistant specializing in suggesting minimum grocery items for common children's symptoms.
                    Given a symptom, provide a short list of the most essential items to purchase to create home remedies.
                    Focus on basic, widely available ingredients.
                    Respond in a simple, comma-separated list format.
                    Example: "Honey, Lemon, Ginger"
                    """



            response = model.generate_content(
                [user_prompt_shop, model_prompt_shop],
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                )
            )

            shopping_list = response.text.strip()
            print(shopping_list)
            # Calculate and print costs
            total_tokens = response.usage_metadata.total_token_count
            prompt_tokens = response.usage_metadata.prompt_token_count
            completion_tokens = response.usage_metadata.candidates_token_count

            input_cost = (prompt_tokens / 1000) * COST_PER_1000_INPUT_TOKENS
            output_cost = (completion_tokens / 1000) * COST_PER_1000_OUTPUT_TOKENS
            total_cost = input_cost + output_cost

            print(f"Total tokens used: {total_tokens}")
            print(f"Tokens used for the prompt: {prompt_tokens}")
            print(f"Tokens used for the completion: {completion_tokens}")
            print(f"Prompt Tokens Cost: ${input_cost:.6f}")
            print(f"Completion Tokens Cost: ${output_cost:.6f}")
            print(f"Total Cost: ${total_cost:.6f}")


            return shopping_list

        except Exception as e:
            print(f"Error calling Gemini API for shopping list: {e}")
            return "Error: Could not generate shopping list."

    try:

            remedy_data_str = response.text.strip()
            remedy_data_str = remedy_data_str.replace("```json", "").replace("```", "").strip()

            try:
                json_data = json.loads(remedy_data_str)
                # Extract the remedy data from the 'properties' dictionary
                remedy_info = {}
                if "properties" in json_data:
                    remedy_info["remedy_name"] = json_data["properties"]["remedy_name"]["title"]
                    remedy_info["steps"] = json_data["steps"]
                else:
                    print("properties key not found")
                print("json:::",json_data)
                remedy_data = RemedyInstruction.model_validate(remedy_info)
                print(f"Remedy Name: {remedy_data.remedy_name}")
                print(f"Remedy_Steps::", remedy_data.steps)
                return remedy_data
            except json.JSONDecodeError as json_err:
                print(f"JSON Decode Error: {json_err}")
                print(f"Recieved String: {remedy_data_str}")
                return None
    except ValidationError as e:
            print(f"Error parsing remedy instructions: {e}")
            return None
    except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None


def main():
    # Example usage
    symptom = "Ear Pain"
    ingredients = ["coconut"]
    allergies = []
    remedy = generate_remedy_instructions(symptom, ingredients, allergies, temperature=0.3, max_output_tokens=512)


if __name__ == "__main__":
    main()