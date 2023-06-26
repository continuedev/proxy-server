import json
from typing import Any, Dict, List, Union
from fastapi import FastAPI, Request, Depends, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import openai
from os import getenv
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
app = FastAPI(debug=True)

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

CHAT_MODELS = {
    "gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4", "gpt-3.5-turbo-0613"
}


class RequestBody(BaseModel):
    unique_id: str

    messages: List[Any]
    model: str

    max_tokens: int = 2048
    temperature: float = 0.5
    top_p: float = 1
    frequency_penalty: float = 0
    presence_penalty: float = 0
    n: int = 1
    functions: Any = None
    function_call: Any = None
    stop: Any = None
    logit_bias: Dict[str, float] = None
    user: str = None


def check_valid_args(body: RequestBody) -> Any:
    if body.model not in CHAT_MODELS:
        raise ValueError(f"Invalid model: {body.model}")

    if body.unique_id not in requests_from_clients:
        requests_from_clients[body.unique_id] = 1
    elif requests_from_clients[body.unique_id] > 1000:
        raise ValueError(
            "Too many requests from this client (limit is 1000). You can try using your own API key to get unlimited usage.")
    return body.dict(exclude={"unique_id"}, exclude_none=True)


@app.post("/complete")
async def complete(body: RequestBody):
    args = check_valid_args(body)

    try:
        resp = await openai.ChatCompletion.acreate(**args)
        return resp.choices[0].message.content
    except:
        raise HTTPException(
            status_code=500, detail="This model is currently overloaded. Please try again.")


@app.post("/stream_complete")
async def stream_complete(body: RequestBody):
    args = check_valid_args(body)
    args["stream"] = True

    async def stream_response():
        try:
            async for chunk in await openai.ChatCompletion.acreate(**args):
                if "content" in chunk.choices[0].delta:
                    yield chunk.choices[0].delta.content
                else:
                    continue
        except:
            raise HTTPException(
                status_code=500, detail="This model is currently overloaded. Please try again.")
    return StreamingResponse(stream_response(), media_type="text/plain")


@app.post("/stream_chat")
async def stream_chat(body: RequestBody):
    args = check_valid_args(body)
    args["stream"] = True

    if not args["model"].endswith("0613") and "functions" in args:
        del args["functions"]

    async def stream_response():
        try:
            async for chunk in await openai.ChatCompletion.acreate(**args):
                yield json.dumps(chunk.choices[0].delta) + "\n"
        except:
            raise HTTPException(
                status_code=500, detail="This model is currently overloaded. Please try again.")

    return StreamingResponse(stream_response(), media_type="text/plain")
