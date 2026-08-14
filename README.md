# MedRAGAssistant

Medical RAG (Retrieval-Augmented Generation) chatbot — FastAPI backend + Streamlit frontend, with LangChain, Pinecone, and Groq/LLaMA.

---

*N.B* This project is still work in progress. Claude code is used as an assistant vibe coder for this project, all evaluations on assisted dev based developments will be reported later as part of the work carried out in this project. For now, author is using pure programming judgement protocol to assess Claude's contribution

## Improvements and Unique Contributions

-- This section includes all new workarounds I have discovered while implementing the project.

In our project we explicitly handle environment variables using pydantic_settings' `settings.X` as opposed to `os.getenv()` for setting API keys and environment variables in general. This gives us the added benefit that:
