from openai import OpenAI
from dotenv import load_dotenv
import json
import os


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL")
base_url = os.getenv("OPENAI_BASE_URL")

def llm_structure(instruction:str):
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": instruction},],
        response_format={"type": "json_object"},)
    return json.loads(response.choices[0].message.content)

def llm(instruction:str):
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": instruction},],)
    return response.choices[0].message.content

def parsed_user_data(data: str) -> dict:
    
    prompt = f"""
    Convert the following natural language into a valid, well-structured JSON object.
    Rules:
    - Output ONLY JSON (no text, no markdown)
    - Use clear, semantic keys
    - Preserve all information from the input
    - Use arrays for lists and nested objects where appropriate
    - Use null for missing or unknown values

    Input:
    {data}
    """

    response = llm_structure(prompt)
    return response
    
    