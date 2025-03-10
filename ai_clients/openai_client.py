import json
import os
from typing import List, Optional
from pydantic import BaseModel, ValidationError
from typing import List
import openai
from dill.source import indent
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
print(client)

# Specify the model to use
model = "gpt-4o-mini"


def generate_remedy_instructions(symptom: str, available_ingredients: list, allergies: list = None):
    """
    Calls OpenAI API to generate kitchen remedy instructions based on the given symptom and available ingredients.

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
        response = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system",
                 "content": f"""You are a professional medical assistant specializing in home remedies for children's common illnesses.
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
                                           """},

                {"role": "user",
                 "content": f"My child has {symptom}. What home remedy can I use? "
                            f"I have these ingredients: {', '.join(filtered_ingredients) if filtered_ingredients else 'none'}."}
            ],
            temperature=0.3,
            max_tokens=256
        )
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "Error: OpenAI API call failed."
    # Example pricing (adjust based on actual rate for "gpt-4o-mini")
    COST_PER_1000_INPUT_TOKENS = 0.15 / 1000  # $0.15 per million input tokens
    COST_PER_1000_OUTPUT_TOKENS = 0.60 / 1000  # $0.60 per million output tokens

    # Extract token usage from response
    total_tokens = response.usage.total_tokens
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens

    # Calculate cost
    input_cost = (prompt_tokens / 1000) * COST_PER_1000_INPUT_TOKENS
    output_cost = (completion_tokens / 1000) * COST_PER_1000_OUTPUT_TOKENS

    # Total cost
    total_cost = input_cost + output_cost
    # Print token usage
    print(f"Total tokens used: {total_tokens}")
    print(f"Tokens used for the prompt: {prompt_tokens}")
    print(f"Tokens used for the completion: {completion_tokens}")
    # Print the cost breakdown
    print(f"Prompt Tokens Cost: ${input_cost:.6f}")
    print(f"Completion Tokens Cost: ${output_cost:.6f}")
    print(f"Total Cost: ${total_cost:.6f}")


    # Parse the response into a structured format (RemedyInstruction model)
    remedy_data_str = response.choices[0].message.content.strip()

    print("remedy_preethi::",type(remedy_data_str))
    if "No remedy possible with available ingredients." in remedy_data_str:
        try:
            print("inside afwef")
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system",
                     "content": f"""You are a helpful assistant specializing in suggesting minimum grocery items for common children's symptoms.
                                              Given a symptom, provide a short list of the most essential items to purchase to create home remedies.
                                              Focus on basic, widely available ingredients.
                                              Respond in a simple, comma-separated list format.
                                              Example: "Honey, Lemon, Ginger"
                                              """},
                    {"role": "user",
                     "content": f"My child has {symptom}. What are the minimum items I should buy?"}
                ],
                temperature=0.5,
                max_tokens=100
            )

            shopping_list = response.choices[0].message.content.strip()
            print(shopping_list)
            return shopping_list

        except Exception as e:
            print(f"Error calling OpenAI API for shopping list: {e}")
            return "Error: Could not generate shopping list."
    else:
      try:
         print(f"remedy_name::",remedy_data_str)
         remedy_data = RemedyInstruction.model_validate_json(remedy_data_str)
         print(f"Remedy Name: {remedy_data.remedy_name}")
         print(f"Remedy_Steps::",remedy_data.steps)
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
