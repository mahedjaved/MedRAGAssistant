#!/usr/bin/env python3
"""Evaluation harness for MedRAGAssistant using RAGAS metrics.
Usage:
    cd /path/to/MedRAGAssistant
    python scripts/run_evaluation.py
Requires:
    - PINECONE_API_KEY and GROQ_API_KEY in .env or environment
    - OPENAI_API_KEY for RAGAS metric computation (v0.2+)
    - Medical PDFs already indexed in Pinecone (via /upload_pdfs/)
    - ragas, datasets, pandas installed
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
# Add project root to Python path so we can import server modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "server"))

from config import settings
from modules.load_vectorstore import embedding_model, PINECONE_INDEX_NAME
from modules.llm import get_llm_chain
from logger import logger

# Import Pinecone for direct query (same pattern as ask_question.py)
from pinecone import Pinecone
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field
from typing import List, Optional


def load_test_dataset(path: str) -> list[dict]:
    """
    Loads questions and answers pairs from the JSONL file in tests/test_data with each line a JSON object with:
        question(str): the user's query
        answer(str): the expected gold answer
        contexts(list[str]): relevant document snippets
        ground_truth(str): authoritative answer
    """
    questions = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))
    logger.info(f"Loaded {len(questions)} test questions from {path}")
    return questions


def get_retriever_for_question(question: str) -> tuple:
    """
    Replicate the query pattern from ask_question.py.
    Returns a tuple of (retriever, contexts) for the given question.
    """
    # Initialize Pinecone and get index
    pc = Pinecone(api_key=settings.pinecone_api_key)
    index = pc.Index(PINECONE_INDEX_NAME)
    
    # Embed the query
    embedding_query = embedding_model.embed_query(question)
    
    # Query Pinecone directly
    response = index.query(
        vector=embedding_query,
        top_k=3,
        include_metadata=True,
    )
    
    # Build documents from matches
    docs = [
        Document(
            page_content=match["metadata"].get("text", ""),
            metadata=match["metadata"],
        )
        for match in response["matches"]
    ]
    
    # Simple retriever class (same as in ask_question.py)
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
    contexts = [doc.page_content for doc in docs]
    
    return retriever, contexts


def run_evaluation() -> dict:
    """
    Run RAGAS evaluation on the test dataset.
    Returns a report dict with:
        - timestamp: ISO datetime
        - scores: dict of metric_name -> float
        - num_questions: int
        - config: dict of experiment configuration
    """
    dataset_path = project_root / "tests" / "test_data" / "medical_qa.jsonl"
    eval_reports_dir = project_root / "eval_reports"
    eval_reports_dir.mkdir(exist_ok=True)

    # --------------- Load test dataset ------------------ #
    test_questions = load_test_dataset(str(dataset_path))
    
    if not test_questions:
        logger.error("No test questions loaded -- exiting.")
        return {}
    
    # -------- Run queries and collect results --------------- #
    results = []
    for i, item in enumerate(test_questions):
        question = item["question"]
        logger.info(f"[{i + 1}/{len(test_questions)}] {question[:80]}…")
        try:
            # Get retriever and contexts (replicates ask_question.py pattern)
            retriever, contexts = get_retriever_for_question(question)
            
            # Initialize LLM chain
            llm_chain = get_llm_chain(retriever)
            
            # Generate the answer
            result = llm_chain.invoke({"query": question})
            answer = result["result"]

            results.append({
                "question": question,
                "answer": answer,
                "contexts": contexts,
                "ground_truth": item.get("ground_truth", ""),
            })

            logger.info(f"Answer: {answer[:80]} ...")

        except Exception as e:
            logger.error(f" x Failed with: {e}")
            results.append({
                "question": question,
                "answer": "",
                "contexts": [],
                "ground_truth": item.get("ground_truth", ""),
            })

    # -------- Build RAGAS dataset --------------- #
    dataset = Dataset.from_list([{
        "question": r["question"],
        "answer": r["answer"],
        "contexts": r["contexts"],
        "ground_truth": r["ground_truth"],
    } for r in results
    ])

    # -------- Compute RAGAS metrics --------------- #
    logger.info("Computing RAGAS metrics ...")
    
    # Set OpenAI API key for RAGAS if available
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    
    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
    scores = evaluate(dataset, metrics=metrics)

    # -------- Build report --------------- #
    report = {
        "timestamp": datetime.now().isoformat(),
        "scores": {str(k): float(v) for k, v in scores.items()},
        "num_questions": len(results),
        "config": {
            "embeddings": "all-mpnet-base-v2",
            "llm": "llama-3.3-70b-versatile",
            "vector_store": "pinecone",
            "retriever_k": 3,
        },
    }

    # -------- Save report to file --------------- #
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = eval_reports_dir / f"eval_{timestamp}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    # --- Print summary ---
    print("\n" + "=" * 55)
    print("  EVALUATION RESULTS")
    print("=" * 55)
    for metric, score in report["scores"].items():
        print(f"  {metric:<22} {score:.4f}")
    print(f"\n  Questions:       {report['num_questions']}")
    print(f"  Report saved to: {report_path}")
    print("=" * 55)
    return report

if __name__ == "__main__":
    try:
        run_evaluation()
    except Exception as e:
        logger.exception(f"Evaluation failed: {e}")
        sys.exit(1)