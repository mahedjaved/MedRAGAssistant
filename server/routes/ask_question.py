import os
from re import match

from fastapi import ApiRouter, Form
from fastapi.responses import JSONResponse

from modules.llm import get_llm_chain
from modules.load_vectorstore import load_vectorstore

from langchain_core.documents import Document
from langchain.schema import BaseRetriever

from langchain.google_genai import GoogleGenerativeAIEmbeddings

from pinecone import Pinecone, Index
from pydantic import Field

from typing import List, Optional
from logger import logger

router = ApiRouter()


@router.post("/ask/")
async def ask_question(question: str = Form(...)):
    try:
        logger.info(f"Received question: {question}")
        # index the vectorstore
        pinecone = Pinecone(
            api_key=os.getenv("PINECONE_API_KEY"),
            environment=os.getenv("PINECONE_ENVIRONMENT"),
        )
        index = Index(os.getenv("PINECONE_INDEX_NAME"))
        embed_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        embedding_query = embed_model.embed_query(question)
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
        result = llm_chain.run(question)

        logger.info(f"Generated answer: {result[0:100]}")

        return result

    except Exception as e:
        logger.exception(f"Error processing question: {e}")
        return JSONResponse(
            content={"error": "Failed to process question"}, status_code=500
        )
