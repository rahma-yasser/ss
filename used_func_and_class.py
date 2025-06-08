import json
import re
import typing_extensions as typing
from google import genai
from pydantic import BaseModel
# import textwrap
# import time
# from dotenv import load_dotenv
import os

# load_dotenv()  # Load variables from .env

# KEY = os.getenv("API_KEY")
KEY="AIzaSyAoEnHcllqAerkW7yxfUlUYcAlZRgoOwOg"

# print(f"My API Key is: {api_key}")  # For testing only (remove in production)


client = genai.Client(api_key=KEY)


class skill_breakdownc(BaseModel):
    clarity: int
    example_quality: int
    structure: int
    outcome: int
# typing.TypedDict
class evaluation_info(BaseModel):
    score: int
    skill_breakdown: skill_breakdownc
    strengths: typing.List[str]
    weaknesses: typing.List[str]
    feedback: str

def parse_response(text):
    """Robust JSON parsing with error handling"""
    try:
        cleaned = re.sub(r'[\x00-\x1F]|```json|\```', '', text)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        print(f"Failed to parse: {text[:200]}...")
        return {"error": "Evaluation failed"}
    
def evaluate_response(question ,answer, target_skill):
    """this returns json formated string of user's evaluation"""
    
    prompt = f"""
    You are a soft skills interviewer evaluating a user's response.

    Your role is to assess how reasonably and relevantly the response reflects the skill: **{target_skill}**.

    Use the schema provided to guide your evaluation. Each requirement must be completed.

    - Keep your tone supportive, understanding, and concise.
    - Focus more on how well the response reflects an **attempt** to demonstrate the skill, rather than perfection.
    - If the response is unrelated or completely off-topic, give a lower evaluation.
    - Do not leave any field empty.
    - All numeric scores must be between 0 and 10, based on overall effort, clarity, and relevance.

    Question: {question}

    Response: {answer}
    """


    response=client.models.generate_content(model="gemini-2.0-flash",contents=[prompt], config={"response_mime_type": "application/json","response_schema":evaluation_info })
    # return response.text , response.usage_metadata.total_token_count
    return response.text





