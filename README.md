# MedRAGAssistant

Medical RAG (Retrieval-Augmented Generation) chatbot — FastAPI backend + Streamlit frontend, with LangChain, Pinecone, and Groq/LLaMA.

---

## Improvements and Unique Contributions

### In our project we explicitly handle environment variables using pydantic_settings' `settings.X` as opposed to `os.getenv()` for setting API keys and environment variables in general. This gives us the added benefit that:

### 1. Type coercion : catches mistakes at startup

```python
# os.getenv — stringly typed, silent failures
port = int(os.getenv("API_PORT", "8000"))       # crashes at use time
log_level = os.getenv("LOG_LEVEL", "INFO")      # misspelling never caught
langsmith_tracing = bool(os.getenv("LANGSMITH_TRACING"))  # always True! (non-empty string is truthy)

# Pydantic Settings — typed at the border
api_port: int = 8000             # "eight-thousand" → ValidationError at import
log_level: str = "INFO"          # fine
langsmith_tracing: bool = False   # "false" → False, "true" → True, "1" → True
```

`bool(os.getenv("X"))` is a notorious footgun, any non-empty string is `True` regardless of its value. Pydantic handles that correctly.

### 2. Fail fast : one error message, not a crash mid-request

With `os.getenv`, a missing `PINECONE_API_KEY` isn't discovered until someone sends their first query and the code path hits `Pinecone(api_key=None)`. That's a 500 error returned to a user.

With `Settings()`, the app **refuses to start** if a required field is missing:

```
pydantic_settings.sources.PydanticSettingsError: 
  field "pinecone_api_key" is required
```

It fails on `uvicorn` startup, not at 3am when a user asks a question!

### 3. Single source of truth : one look tells you everything

A file with `os.getenv()` calls scattered across 5 modules means you have to grep the entire codebase to know what env vars exist, which are required, what their defaults are.

```python
# server/config.py — the complete inventory, one screen
class Settings(BaseSettings):
    pinecone_api_key: str        # required — app won't start without it
    groq_api_key: str            # required
    log_level: str = "INFO"      # optional with default
    ...
```

Every env var the app uses is documented in one place. This enhances reproducibility as future contributers can see the full API surface in 30 seconds.

### 4. IDE autocompletion : less context switching

```python
# os.getenv — no help from your editor
api_key = os.getenv("PINE...")  # did I spell it right? PINEAPPLE_API_KEY?

# settings — autocomplete works
settings.pinecone_api_key        # editor tells you the type and default
settings.groq_api_key_resolved   # property docs shown inline
```

### 5. Immutability : prevents runtime corruption

`os.environ` is a mutable dict, any module can do `os.environ["PINECONE_API_KEY"] = "hacked"` at runtime. Pydantic Settings produces a frozen object by default (with `frozen=True` in the config). Once loaded, it's read-only.

### When `os.getenv()` is actually fine

- **One-off scripts** that don't warrant a config class
- **CLI tools** with a single env var
- Anywhere you don't need type coercion, validation, or documentation

But for a **production multi-service app** with 10+ env vars across 5 modules, the value compounds quickly. The startup validation alone is worth the switch — you want to know your config is broken *before* you deploy, not after.
