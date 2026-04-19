
### 아키텍처 ###
```
사용자
  ↓ HTTP
Open WebUI (프론트엔드)
  ↓ OpenAI-compatible API (/v1/chat/completions)
FastAPI (OpenAI API 호환 레이어)
  ↓ invoke()
LangGraph Agent (워크플로우)
  ├─ Tool: RAGSearch (Milvus)
  ├─ Tool: web_fetch
  ├─ Tool: ...
  └─ Bedrock (LLM)
```
#### 필수 구현해야 할 3개 엔드포인트 ####
* GET  /v1/models              → 사용 가능한 모델 목록
* POST /v1/chat/completions    → 실제 채팅 (stream / non-stream 모두)
* GET  /health                 → 헬스체크 (선택이지만 권장)


## FastAPI + LangGraph ##
```
import json
import time
import uuid
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langgraph.graph import StateGraph
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# (여기서는 간단히 구조만. 실제 LangGraph 에이전트는 별도 모듈로 분리 추천)
from my_agent import build_agent   # LangGraph 워크플로우 빌드 함수


app = FastAPI(title="Agentic AI Gateway")

# 에이전트는 프로세스 시작 시 한 번만 빌드
agent = build_agent()


# ---------- Pydantic 모델 (OpenAI 스펙) ----------

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    stream: bool = False
    temperature: float | None = 0.2
    max_tokens: int | None = None


# ---------- /v1/models ----------

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "agentic-rag",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "workshop",
            }
        ],
    }


# ---------- /v1/chat/completions ----------

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    # OpenAI 메시지 → LangChain 메시지로 변환
    lc_messages = []
    for m in req.messages:
        if m.role == "system":
            lc_messages.append(SystemMessage(content=m.content))
        elif m.role == "user":
            lc_messages.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            lc_messages.append(AIMessage(content=m.content))

    if req.stream:
        return StreamingResponse(
            stream_agent(lc_messages, req.model),
            media_type="text/event-stream",
        )

    # Non-stream: 한 번에 결과 반환
    result = await agent.ainvoke({"messages": lc_messages})
    answer = result["messages"][-1].content

    return {
        "id": f"chatcmpl-{uuid.uuid4()}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": answer},
            "finish_reason": "stop",
        }],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }


# ---------- 스트리밍 ----------

async def stream_agent(messages, model: str) -> AsyncIterator[str]:
    """LangGraph의 astream으로 토큰 단위 스트리밍."""
    chat_id = f"chatcmpl-{uuid.uuid4()}"
    created = int(time.time())

    # LangGraph가 노드 단위로 결과를 흘려보냄
    async for chunk in agent.astream(
        {"messages": messages},
        stream_mode="messages",   # 토큰 단위
    ):
        # chunk 구조는 LangGraph 설정에 따라 다름
        # 예시: (message_chunk, metadata) 튜플
        if isinstance(chunk, tuple):
            msg_chunk = chunk[0]
            content = getattr(msg_chunk, "content", "")
        else:
            content = str(chunk)

        if not content:
            continue

        payload = {
            "id": chat_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {"content": content},
                "finish_reason": None,
            }],
        }
        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    # 마지막에 종료 시그널
    done_payload = {
        "id": chat_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    yield f"data: {json.dumps(done_payload)}\n\n"
    yield "data: [DONE]\n\n"


# ---------- 헬스체크 ----------

@app.get("/health")
async def health():
    return {"status": "ok"}
```
