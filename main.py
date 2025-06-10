import json
from google import genai
from fastapi import FastAPI , Request , WebSocket
from pydantic import BaseModel
import os
import asyncio
# import contextlib
import pandas as pd
import typing_extensions as typing

import re

covered_soft_skills = [
    "Communication", "Teamwork", "Conflict Resolution",
    "Time Management", "Adaptability", "Leadership",
    "Problem Solving", "Emotional Intelligence"
]
KEY="AIzaSyAoEnHcllqAerkW7yxfUlUYcAlZRgoOwOg"



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
    return response.text




app=FastAPI()
@app.get("/")
async def root():
    return {"this is home page":"follow next"}

@app.websocket("/soft/{num_q}")
async def soft(num_q, websocket: WebSocket):
    evaluation=[]
    prompt = (
            "You are soft skills interviewer asking related questions to user answers"
            "make it like real life soft skills interview conversation"
            "The question should be based on the previous user answer. "
            f"Here are the soft skills you should ask about: {', '.join(covered_soft_skills)}. note you it is okay to ask from them randomly depending on the user previous answer"
            "Avoid asking about the same soft skill again. "
            "Return the result in JSON format as {question: str ,target_skill: str}."

            "Now you should start with just the question avoid adding any other text"
        )
    interviewer = client.chats.create(model="gemini-2.0-flash")
    await websocket.accept()
    answer = ""
    questions = []

    async def keep_alive():
        try:
            while True:
                await websocket.send_json({"type": "ping"})
                print("Ping sent")
                await asyncio.sleep(20)
        except Exception as e:
            print(f"Keep-alive stopped: {e}")

    ping_task = asyncio.create_task(keep_alive())

    try:
        for i in range(int(num_q)):
            print("**" * 100)
            if not questions:
                interviewer_question_parced = parse_response(interviewer.send_message(prompt).text)
            else:
                interviewer_question_parced = parse_response(interviewer.send_message(answer).text)

            questions.append(interviewer_question_parced)
            await websocket.send_json(interviewer_question_parced)

            recev = await websocket.receive_json()
            answer = recev.get("text")
            evaluate=evaluate_response(interviewer_question_parced["question"],answer,interviewer_question_parced["target_skill"])
            evaluation.append(json.loads(evaluate))
            evaluationJson=evaluate
            await websocket.send_json(evaluationJson) 
            await asyncio.sleep(20)
        df=pd.json_normalize(evaluation)
        avgs=df.select_dtypes(include='number').mean().to_json(indent=4)
        await websocket.send_json(avgs)
    finally:
        ping_task.cancel()
        try:
            await ping_task
        except asyncio.CancelledError:
            pass

    print("#"*50)
