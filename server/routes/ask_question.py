import time
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Form, HTTPException

from schemas import QuestionRequest, QuestionResponse

from modules import cache
from modules.rate_limiter import limiter
from modules.llm import get_llm_chain
from modules.db_logger import log_query, estimate_tokens_and_cost


# from modules.load_vectorstore import load_vectorstore, PINECONE_INDEX_NAME
from modules.load_vectorstore import (
    load_vectorstore,
    embedding_model,
    PINECONE_INDEX_NAME,
)
from modules.langsmith_tracing import configure_langsmith_tracing, end_langsmith_run

from modules.metrics import (
    request_count,
    token_usage,
    chunk_count,
    errors,
    request_latency,
    query_latency,
    active_requests,
)

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from pinecone import Pinecone
from pydantic import Field

from typing import List, Optional
from logger import logger
from config import settings
from modules.prompt_injection_detector import

router = APIRouter()

@router.post("/ask/", response_model=QuestionResponse)
@limiter.limit("10/minute")
async def ask_question(question: str = Form(...)):
    try:
        validated = QuestionRequest(question=question)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    req_start_time = time.time()
    active_requests.labels(method="POST", endpoint="/ask/").inc()

    try:
        logger.info(f"Received question: {validated.question}")
        # index the vectorstore
        pc = Pinecone(
            api_key=settings.pinecone_api_key,
        )
        index = pc.Index(PINECONE_INDEX_NAME)
        embedding_quer12y = embedding_model.embed_query(validated.question)
        response = index.query(
            vector=embedding_query,
            top_k=3,  # top 3 relevant chunks
            include_metadata=True,
        )
        # Retrieve the docs
        docs = [
            Document(
                page_content=match["metadata"].get("text", ""),
                metadata=match["metadata"],
            )
            for match in response["matches"]
        ]


        # Simple retriever class
        class SimpleRetriever(BaseRetriever):
            tags: Optional[List[str]] = Field(
                default_factory=list, description="Optional tags for filtering"
            )
            metadata: Optional[dict] = Field(
                default_factory=dict, description="Optional metadata for filtering"
            )

            def __init__(self, documents: List[Document]):
                super().__init__()
                self._docs = documents

            def _get_relevant_documents(self, query: str) -> List[Document]:
                return self._docs

        retriever = SimpleRetriever(docs)
        llm_chain = get_llm_chain(retriever)
        tracer = None  # Initialize tracer variable

        try:
            # setup langsmith tracing
            tracer = configure_langsmith_tracing(
                "med-rag-assistant",
                inputs={"question": validated.question},
                tags=["RAG", "medrag-assistant"],
            )

        except Exception as e:
            errors.labels(method="POST", endpoint="/ask/", status_code=500).inc()
            logger.exception(f"Error setting up langsmith tracing: {e}")

        query_start = time.time()
        result = llm_chain.invoke({"query": validated.question})
        query_latency.labels(method="POST", endpoint="/ask/").observe(
            time.time() - query_start
        )

        end_langsmith_run(
            tracer,
            outputs={"result": result["result"]},
            error=e if "e" in locals() else None,
        )

        # update Prometheus metrics
        request_count.labels(method="POST", endpoint="/ask/", status_code=200).inc()
        token_usage.labels(method="POST", endpoint="/ask/").inc(
            len(result["result"].split())
        )
        chunk_count.labels(method="POST", endpoint="/ask/").inc(len(docs))
        request_latency.labels(method="POST", endpoint="/ask/").observe(
            time.time() - req_start_time
        )

        logger.info(f"Generated answer: {result['result'][0:100]}")

        # estimate tokens and cost
        estimated_input_tokens, estimated_output_tokens, estimated_cost = (
            estimate_tokens_and_cost(validated.question, result["result"])
        )

        # log the query, answer, sources and token costs to the database
        await log_query(
            query=validated.question,
            answer=result["result"],
            sources=[doc.metadata.get("source", "Unknown") for doc in docs],
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            estimated_cost=estimated_cost,
        )

        sources = [
            doc.metadata.get("source", "Unknown")
            for doc in docs
        ]

        return QuestionResponse(
            response=result["result"],
            sources=sources,
        )

    except Exception as e:
        logger.exception(f"Error processing question: {e}")
        errors.labels(method="POST", endpoint="/ask/", status_code=500).inc()
        return JSONResponse(
            content={"error": "Failed to process question"}, status_code=500
        )

    finally:
        active_requests.labels(method="POST", endpoint="/ask/").dec()
