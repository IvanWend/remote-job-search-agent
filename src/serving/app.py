import os
from collections.abc import AsyncIterator

import psycopg
from anyio import to_thread
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.agent.loop import build_agent
from src.serving.sse import sse_event, stream_answer

load_dotenv()

url = os.environ["DATABASE_URL"]


class AskRequest(BaseModel):
    question: str


def _connect() -> psycopg.Connection:
    return psycopg.connect(url)


async def _stream(question: str) -> AsyncIterator[str]:
    conn: psycopg.Connection | None = None
    try:
        conn = await to_thread.run_sync(_connect)
        agent = build_agent(conn=conn)
        async for frame in stream_answer(agent, question):
            yield frame
    except Exception as e:
        yield sse_event("error", {"message": str(e)})
    finally:
        if conn is not None:
            await to_thread.run_sync(conn.close)


def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/ask")
    def ask_get(q: str):
        return StreamingResponse(_stream(q), media_type="text/event-stream")

    @app.post("/ask")
    def ask_post(request: AskRequest):
        return StreamingResponse(_stream(request.question), media_type="text/event-stream")

    return app


app = create_app()
