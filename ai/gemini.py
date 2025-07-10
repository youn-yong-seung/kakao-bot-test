from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
import os

def gemini_free(system_instruction:str, prompt: str):
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    model_id = "gemini-2.0-flash-lite"

    response = client.models.generate_content(
        model=model_id,
        config=GenerateContentConfig(
            system_instruction=system_instruction,
            response_modalities=["TEXT"],
        ),
        contents=prompt
    )
    content = response.text.replace('*', '')
    return content

def gemini20_googlesearch(system_instruction:str, prompt: str):
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    model_id = "gemini-2.0-flash"

    google_search_tool = Tool(
        google_search = GoogleSearch()
    )

    response = client.models.generate_content(
        model=model_id,
        config=GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[google_search_tool],
            response_modalities=["TEXT"],
        ),
        contents=prompt
    )

    content = ''
    for each in response.candidates[0].content.parts:
        content += each.text.replace('*', '').strip()

    return content