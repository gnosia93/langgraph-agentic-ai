import os
from functools import lru_cache
from mcp.server.fastmcp import FastMCP
from RAGSearch import RAGSearch


# MCP 서버 초기화
mcp = FastMCP("rag-search")


@lru_cache(maxsize=1)
def get_rag() -> RAGSearch:
    """RAGSearch 싱글턴. 첫 호출 시에만 생성되며 thread-safe."""
    return RAGSearch(
        host=os.getenv("MILVUS_HOST", "localhost"),
        port=os.getenv("MILVUS_PORT", "19530"),
        collection_name=os.getenv("MILVUS_COLLECTION", "papers"),
        bedrock_model_id=os.getenv(
            "BEDROCK_MODEL_ID",
            "anthropic.claude-3-5-sonnet-20241022-v2:0",
        ),
        aws_region=os.getenv("AWS_REGION", "us-west-2"),
    )


@mcp.tool()
def search_papers(query: str, top_k: int = 20, top_n: int = 5) -> dict:
    """
    논문 벡터 DB(Milvus)에서 질의와 관련된 청크를 검색하고,
    Bedrock LLM으로 근거 기반 답변을 생성합니다.

    Args:
        query: 검색할 자연어 질문
        top_k: Milvus에서 가져올 후보 청크 수 (기본 20)
        top_n: 재순위 후 LLM에 넘길 청크 수 (기본 5)

    Returns:
        answer, contexts(출처 문서명/페이지 포함)
    """
    rag = get_rag()
    result = rag.query(query, top_k=top_k, top_n=top_n)
    contexts = [
        {
            "doc_name": c["doc_name"],
            "page": c["page"],
            "rerank_score": round(c["rerank_score"], 3),
            "text": c["text"][:300] + ("..." if len(c["text"]) > 300 else ""),
        }
        for c in result["contexts"]
    ]
    return {"answer": result["answer"], "contexts": contexts}


@mcp.tool()
def retrieve_only(query: str, top_k: int = 10) -> list[dict]:
    """
    LLM 호출 없이 벡터 검색 + 재순위 결과만 반환합니다.
    원문 확인이나 디버깅에 유용합니다.
    """
    rag = get_rag()
    hits = rag.retrieve(query, top_k=top_k)
    reranked = rag.rerank(query, hits, top_n=top_k)
    return [
        {
            "doc_name": h["doc_name"],
            "page": h["page"],
            "score": round(h["score"], 3),
            "rerank_score": round(h["rerank_score"], 3),
            "text": h["text"],
        }
        for h in reranked
    ]


if __name__ == "__main__":
    # stdio 모드: MCP 클라이언트가 subprocess로 실행
    mcp.run()
