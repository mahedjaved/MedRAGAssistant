# Medical AI System Architecture

## Overview
This architecture shows a retrieval-augmented generation (RAG) medical AI system built around PDF ingestion, text chunking, embeddings, vector retrieval, and answer generation. The system exposes a FastAPI backend with upload and query endpoints, and uses a vector database plus an LLM to produce grounded, human-readable answers.

## High-level flow
1. User uploads PDF files.
2. PDFs are loaded and raw text is extracted.
3. Text is split into chunks for context preservation.
4. Chunks are embedded and stored in a vector database.
5. A user query is embedded and matched against the vector store.
6. Retrieved context is passed into the RAG chain.
7. The LLM generates a grounded answer.
8. The backend returns a human-readable response.

## Components

### 1. PDF Upload
- Accepts PDF documents from the user.
- Acts as the ingestion entry point.
- Extracts raw text from uploaded files.

### 2. Text Chunking
- Uses `RecursiveCharacterTextSplitter`.
- Breaks large documents into smaller chunks.
- Preserves context across chunk boundaries.

### 3. Embedding Layer
- Converts text chunks into vector embeddings.
- Example options: Google Generative AI embeddings or Hugging Face embeddings.

### 4. Vector Store
- Stores embeddings for semantic retrieval.
- Example: Pinecone.
- Supports efficient similarity search.

### 5. Query Processing
- Embeds the user’s question.
- Runs similarity search against the vector store.
- Retrieves the most relevant chunks.

### 6. RAG Chain
- Combines retrieved context with a system prompt.
- Uses an LLM such as Groq / LLaMA 3.
- Produces grounded responses.

### 7. Answer Generation
- Formats results in a human-readable way.
- Keeps responses concise and relevant.
- Focuses on grounded answers derived from the source PDFs.

### 8. FastAPI Backend
- Exposes `/upload_pdfs` and `/ask` endpoints.
- Handles document ingestion and question answering.
- Serves as the application API layer.

### 9. Health Check
- `GET /health` endpoint for monitoring and orchestration.
- Checks Pinecone connectivity and Groq API key presence.
- Used by Docker's `HEALTHCHECK` and deployment platforms for auto-restarts.
- Returns `{"status": "...", "version": "1.0", "checks": {...}}`.

### 10. Containerisation
- Multi-stage `Dockerfile` for the FastAPI backend (`server/Dockerfile`).
- Lightweight `Dockerfile` for the Streamlit client (`client/Dockerfile`).
- `docker-compose.yml` orchestrates all services: server, client, Qdrant (vector store), and PostgreSQL.
- Named volumes for persistent data (`qdrant_data`, `postgres_data`, `hf_cache`).
- Environment-based configuration via Pydantic Settings (no hardcoded secrets).

### 11. Infrastructure Services
- **Qdrant**: Alternative vector store for local development (future hybrid search).
- **PostgreSQL**: Relational database reserved for query logging and future features.

## Core stack summary

| Layer | Tool/Framework |
|---|---|
| LLM | Groq (LLaMA 3 70B) |
| Embeddings | Hugging Face (all-mpnet-base-v2, 768d) |
| Vector Store | Pinecone (serverless) |
| Local Vector Store | Qdrant (Docker, for dev) |
| RAG Framework | LangChain |
| Backend API | FastAPI |
| Client UI | Streamlit |
| Config | Pydantic Settings |
| Containerisation | Docker / docker-compose |
| CI/CD | GitHub Actions |
| Deployment | Render / Fly.io |

## Mermaid diagram
```mermaid
flowchart LR
    U[User] --> P[PDF Upload]
    P --> T[Text Chunking]
    T --> E[Embedding Layer]
    E --> V[Vector Store]

    U --> Q[Query Processing]
    Q --> V
    V --> R[RAG Chain]
    R --> A[Answer Generation]

    subgraph Backend[FastAPI Backend]
        UP[/upload_pdfs/]
        AS[/ask/]
        H[/health/]
    end

    Backend --> P
    Backend --> Q
    A --> Backend

    subgraph Infra[Infrastructure]
        PC[Pinecone]
        QD[Qdrant]
        PG[PostgreSQL]
    end

    V -.-> PC
    V -.-> QD
    Backend -.-> PG

    subgraph CI[CI/CD Pipeline]
        GA[GitHub Actions]
    end

    GA --> Backend
```

## API endpoints

### `POST /upload_pdfs/`
- Upload one or more PDF files.
- Extract and chunk text.
- Generate embeddings.
- Store chunks in the vector database.

### `POST /ask/`
- Accept a natural-language question.
- Embed the query.
- Retrieve relevant chunks.
- Generate a grounded answer using the RAG chain.

### `GET /health`
- Returns service status, version, and individual dependency checks.
- Used by Docker HEALTHCHECK and deployment platforms.

## Design goals
- Ground answers in uploaded source documents.
- Keep the response format human-readable.
- Maintain context across long medical documents.
- Make retrieval fast and reliable.
- Separate ingestion, retrieval, and generation clearly.

## Notes
- This design is best suited for a document-grounded medical assistant.
- The system should always be careful not to present itself as a doctor.
- Safety and source grounding are important for medical use cases.