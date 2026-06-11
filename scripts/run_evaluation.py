#!/usr/bin/env python3
"""Evaluation harness for MedRAGAssistant using RAGAS metrics.
Usage:
    cd /path/to/MedRAGAssistant
    python scripts/run_evaluation.py
Requires:
    - PINECONE_API_KEY and GROQ_API_KEY in .env or environment
    - Medical PDFs already indexed in Pinecone (via /upload_pdfs/)
    - ragas, datasets, pandas installed
"""
import json
import sys
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
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import settings
from modules.load_vectorstore import load_vectorstore
from modules.llm import get_llm_chain
from logger import logger

def load_test_dataset(path: str) -> list[dict]:
    """
    Loads questions and answers pairs from the JSONL file in tests/test_data with each line a JSON object with:
        question(str): the user's query
        answer(st):the expected gold answer
        contexts(list[str]):relevant document snippets
        ground_truth(str):authoritative answer
    """
    questions = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))
    logger.info(f"Loaded {len(questions)} test questions from {path}")
    return questions

def run_evaluation() -> dict:
    """
    Run RAGAS evaluation on the test dataset.
    Returns a report dict with:
        - timestamp: ISO datetime
        - scores: dict of metric_name -> float
        - num_questions: int
        - config: dict of experiment configuration
    """
    project_root = Path(__file__).resolve().parent.parent
    dataset_path = project_root / "tests" / "test_data" / "medical_qa.jsonl"
    eval_reports_dir = project_root / "eval_reports"
    eval_reports_dir.mkdir(exist_ok=True)

    # --------------- Load test dataset ------------------ #
    test_questions = load_test_dataset(str(dataset_path))
    
    if not test_questions:
        logger.error("No test questions loaded -- exiting.")
        return {}
    
    # -------- Initialise vector store and retriever ---------- #
    logger.info(f"Initialising vector store ...")
    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    # -------- Initialise LLM chain --------------------------- #
    logger.info(f"Initialising LLM chain ...")
    chain = get_llm_chain(retriever)

     # -------- Run queries and collect results --------------- #
    results = []
    for i, item in enumerate(test_questions):
        question = item["question"]
        logger.info(f"[{i + 1}/{len(test_questions)}] {question[:80]}…")
        try:
            # retrieve 'R' the relevant documents
            retrieved_docs = retriever.invoke(question)
            contexts = [doc.page_content for doc in retrieved_docs]

            # generate 'G the answer
            result = chain.invoke({"query": question})
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
            "retriever_k": 4,
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