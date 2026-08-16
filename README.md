# MedRAGAssistant (WIP)

Medical RAG (Retrieval-Augmented Generation) chatbot — FastAPI backend + Streamlit frontend, with LangChain, Pinecone, and Groq/LLaMA.

---

*N.B* This project is still work in progress. Claude code is used as an assistant vibe coder for this project, all evaluations on assisted dev based developments will be reported later as part of the work carried out in this project. For now, author is using pure programming judgement protocol to assess Claude's contribution

## Improvements and Unique Contributions

-- This section includes all new workarounds I have discovered while implementing the project.

In our project we explicitly handle environment variables using pydantic_settings' `settings.X` as opposed to `os.getenv()` for setting API keys and environment variables in general. This gives us the added benefit that:

## To Explore In Future

- **Upgrade prompt injection detection** from the current lightweight regex heuristic to `guardrails-ai-detect-jailbreak` for more robust jailbreak/role-override detection.
- **Add Presidio-based PII redaction** with custom medical recognizers (`PATIENT_ID`, `INSURANCE_ID`, `PHARMACY_ID`) before embedding queries.
- **Implement retry logic** with exponential backoff for Groq and Pinecone calls via `tenacity`.
- **Add semantic caching** (embedding-similarity + TTL) to reduce redundant LLM calls and cost.
- **Async processing for large PDF uploads** using FastAPI `BackgroundTasks` or Celery/RQ.

## Contact

For feedbacks, please contact mahed95@gmail.com
