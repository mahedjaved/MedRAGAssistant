# MedRAGAssistant (WIP)

Medical RAG (Retrieval-Augmented Generation) chatbot — FastAPI backend + Streamlit frontend, with LangChain, Pinecone, and Groq/LLaMA.

---

*N.B* This project is still work in progress. Claude code is used as an assistant vibe coder for this project, all evaluations on assisted dev based developments will be reported later as part of the work carried out in this project. For now, author is using pure programming judgement protocol to assess Claude's contribution

## Improvements and Unique Contributions

-- This section includes all new workarounds I have discovered while implementing the project.

In our project we explicitly handle environment variables using pydantic_settings' `settings.X` as opposed to `os.getenv()` for setting API keys and environment variables in general. This gives us the added benefit that:

- **Using presidio two-layer pattern recognition & scoring approach** allows us to use primary (strict, high confidence pattern) alongside secondary (looser, low confidence fallback) ways of pattern matching. For now we a.r.b number **0.85** for high confidence and **0.65** for low confidence

## To Explore In Future

- **Upgrade prompt injection detection** from the current lightweight regex heuristic to `guardrails-ai-detect-jailbreak` for more robust jailbreak/role-override detection.
- **Add Presidio-based PII redaction** with custom medical recognizers (`PATIENT_ID`, `INSURANCE_ID`, `PHARMACY_ID`) before embedding queries.
- **Implement retry logic** with exponential backoff for Groq and Pinecone calls via `tenacity`.
- **Add semantic caching** (embedding-similarity + TTL) to reduce redundant LLM calls and cost.
- **Async processing for large PDF uploads** using FastAPI `BackgroundTasks` or Celery/RQ.

## Resources

For any reader interested in learning more on the techniques employed in the project please refer to following links:

[1] Presidio Recognizers : https://dev.to/bspann/building-custom-recognizers-5goe

## Contact

For feedback please contact mahed95@gmail.com

