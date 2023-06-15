from typing import Any, Dict
from fastapi import FastAPI, Request, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import openai
from os import getenv
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

requests_from_clients: Dict[str, int] = {}

MAX_REQUESTS_PER_CLIENT = 1000
MAX_TOKENS_PER_CLIENT = 10e6


def check_valid_request(model: str, unique_id: str):
    if model not in ["gpt-3.5-turbo", "gpt-4"]:
        return False

    if unique_id not in requests_from_clients:
        requests_from_clients[unique_id] = 1
    elif requests_from_clients[unique_id] > 1000:
        return False
    return True


class RequestBody(BaseModel):
    chat_history: Any
    model: str
    unique_id: str


@app.post("/complete")
async def complete(body: RequestBody):
    if not check_valid_request(body.model, body.unique_id):
        return "Invalid request"

    args = {"temperature": 0.5, "model": body.model}

    resp = await openai.ChatCompletion.acreate(
        messages=body.chat_history,
        **args,
    )

    return resp.choices[0].message.content


@app.post("/stream_complete")
async def stream_complete(body: RequestBody):
    if not check_valid_request(body.model, body.unique_id):
        return "Invalid request"

    args = {"temperature": 0.5, "stream": True, "model": body.model}

    async def stream_response():
        async for chunk in await openai.ChatCompletion.acreate(
            messages=body.chat_history,
            **args,
        ):
            if "content" in chunk.choices[0].delta:
                yield chunk.choices[0].delta.content
            else:
                continue

    return StreamingResponse(stream_response(), media_type="text/plain")
