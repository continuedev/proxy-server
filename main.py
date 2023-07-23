import json
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import openai
from os import getenv
from dotenv import load_dotenv
from pydantic import BaseModel, validator

load_dotenv()
app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

requests_from_ips: Dict[str, str] = {}


async def rate_limit_middleware(request: Request, call_next):
    ip_address = request.client.host
    if ip_address not in requests_from_ips:
        requests_from_ips[ip_address] = 1
    elif requests_from_ips[ip_address] > MAX_REQUESTS_PER_CLIENT:
        raise HTTPException(
            status_code=429, detail="Too many requests from this IP address (limit is {})".format(MAX_REQUESTS_PER_CLIENT))
    else:
        requests_from_ips[ip_address] += 1
    response = await call_next(request)
    return response


# Based on the type, use OpenAI or Azure
USING_AZURE = False
AZURE_OPENAI_API_TYPE = getenv("AZURE_OPENAI_API_TYPE", None)
AZURE_OPENAI_DEPLOYMENT_NAME = getenv("AZURE_OPENAI_DEPLOYMENT_NAME", None)
if AZURE_OPENAI_API_TYPE is not None and AZURE_OPENAI_API_TYPE == "azure":
    USING_AZURE = True
    openai.api_type = AZURE_OPENAI_API_TYPE
    openai.api_base = getenv("AZURE_OPENAI_API_BASE")
    openai.api_version = getenv("AZURE_OPENAI_API_VERSION")
    openai.api_key = getenv("AZURE_OPENAI_API_KEY")
else:
    openai.api_key = getenv("OPENAI_API_KEY")


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

    engine: str = None

    @validator("engine", pre=True, always=True)
    def azure_engine(cls, v):
        if USING_AZURE:
            return AZURE_OPENAI_DEPLOYMENT_NAME
        return v

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
        raise HTTPException(
            status_code=429, detail="Too many requests from this client (limit is {})".format(MAX_REQUESTS_PER_CLIENT))
    return body.dict(exclude={"unique_id"}, exclude_none=True)


@app.post("/complete")
async def complete(body: RequestBody):
    args = check_valid_args(body)

    try:
        resp = await openai.ChatCompletion.acreate(**args)
        return resp.choices[0].message.content
    except Exception as e:
        print("Exception in /complete", e)
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
        except Exception as e:
            print("Exception in /stream_complete", e)
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
        except Exception as e:
            print("Exception in /stream_chat", e)
            raise HTTPException(
                status_code=500, detail="This model is currently overloaded. Please try again.")

    return StreamingResponse(stream_response(), media_type="text/plain")
