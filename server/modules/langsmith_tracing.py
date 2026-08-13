"""LangSmith integration for tracing and monitoring RAG chains."""

import os
from typing import Any, Dict, List, Optional
from langsmith import Client


# Initialise Langsmith client
langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
langsmith_tracing = os.getenv("LANGSMITH_TRACING", "true").lower() == "true"
langsmith_project = os.getenv("LANGSMITH_PROJECT", "medrag-assistant")

# Initialize the LangSmith client if tracing is enabled and the API key is provided
if langsmith_tracing and langsmith_api_key:
    _langsmith_client = Client(api_key=langsmith_api_key)
    _langsmith_enabled = True
else:
    _langsmith_client = None
    _langsmith_enabled = False


def configure_langsmith_tracing(
    run_name: str,
    inputs: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
) -> Any:
    """Configure LangSmith tracing for a RAG chain run.

    Args:
        run_name (str): The name of the langsmith run.
        inputs (Dict[str, Any]): The inputs to the RAG chain.
        metadata (Optional[Dict[str, Any]]): Additional metadata for the run.

    Returns:
        LangSmith run object if enabled, None otherwise
    """
    if not _langsmith_enabled or not _langsmith_client:
        return None
    
    run_config = dict(
        name=run_name,
        inputs=inputs,
        metadata=metadata or {},
        tags=tags or [],
        project_name=langsmith_project
    )

    return _langsmith_client.create_run(run_config)

def end_langsmith_run(
        run: Any,
        outputs: Dict[str, Any],
        error: Optional[Exception] = None
):
    """
    End a LangSmith run, logging outputs and any errors.
    
    Args:
        run (Any): The LangSmith run object to end.
        outputs (Dict[str, Any]): The outputs of the RAG chain.
        error (Optional[Exception]): Any exception that occurred during the run.
    """
    if run and _langsmith_client:
        if error:
            _langsmith_client.update_run(
                run.id,
                outputs=outputs,
                error=str(error),
                end_time=None,  # Optionally, you can set the end time here
            )
        else:
            _langsmith_client.update_run(
                run.id,
                outputs=outputs,
                end_time=None,  # Optionally, you can set the end time here
            )
            
def log_metric(metric_name: str, value: float, run: Any = None):
    """
    Log a metric to LangSmith.
    
    Args:
        metric_name: Name of the metric
        value: Metric value
        run: Optional LangSmith run object
    """
    if run and _langsmith_client:
        _langsmith_client.create_evaluation_dataset(
            dataset_name=f"metrics_{metric_name}",
            examples=[{"input": metric_name, "expected_output": str(value)}]
        )