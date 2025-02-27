import openai
from dotenv import load_dotenv
import os
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("open"))

# Specify the model to use
model = "gpt-4o-mini"


def generate_remedy_instructions(symptom: str, available_ingredients: list):
    """
    Calls OpenAI API to generate kitchen remedy instructions based on the given symptom and available ingredients.

    Args:
        symptom (str): The symptom to find a remedy for.
        available_ingredients (list): A list of available ingredients.

    Returns:
        str: AI-generated remedy instructions in SMS format.
    """
    model = "gpt-4o-mini"

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system",
             "content": "You are a professional medical assistant specializing in home remedies for children's illnesses. "
                        "Provide short, step-by-step instructions in SMS format based on symptoms and available ingredients. "
                        "If no ingredients are available or suitable for the symptom, suggest a simple home remedy."},
            {"role": "user",
             "content": f"My child has {symptom}. What should I use from my kitchen to help? "
                        f"I have the following ingredients available: {', '.join(available_ingredients) if available_ingredients else 'none'}."},
            {"role": "user",
             "content": "If no suitable ingredients are found, please suggest a common, easy-to-follow home remedy. "
                        "Provide the instructions as a list in SMS format."}
        ]   ,
        temperature=0.2,
        max_tokens=150
    )
    total_tokens = response.usage.total_tokens
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens


    print(f"Total tokens used: {total_tokens}")
    print(f"Prompt tokens: {prompt_tokens}")
    print(f"Completion tokens: {completion_tokens}")
    return response.choices[0].message.content
