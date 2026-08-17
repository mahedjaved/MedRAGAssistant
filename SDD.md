# MedRAGAssistant — Retrospective Product & Technical Specification

> **Status: retrospective design specification.** This document was reconstructed after implementation from the repository architecture, project guides, and observed code paths. It is not presented as a contemporaneous specification written before development. Its purpose is to make the project’s design intent, implemented choices, constraints, and next validation steps explicit for maintenance and interview discussion.

| Document field | Value |
|---|---|
| Project | MedRAGAssistant |
| Product type | Document-grounded medical-information assistant |
| Primary interaction | Upload medical PDFs and ask natural-language questions about the uploaded corpus |
| Architecture style | Retrieval-augmented generation (RAG) with separated ingestion, retrieval, generation, and operational layers |
| Implementation status | Prototype with production foundations; not a diagnosis, prognosis, prescription, or patient-level prediction product |
| Evidence base | Repository architecture documentation, medical-chatbot guide, production-enhancement phase guide, and verified code review |

## 1. Product intent

MedRAGAssistant exists to make medical-document information easier to query while keeping the document corpus external to the language model. A user supplies PDF material, the system retrieves text judged relevant to a question, and an LLM generates a readable response from that retrieved context. The intended value is **document-grounded informational support**, not autonomous medical judgment.

### 1.1 Problem statement

Generic model responses are difficult to audit when the relevant source material is scattered across long PDFs. The system should create a repeatable path from a user question to retrieved document context and then to a human-readable answer. The response should remain bounded by the project’s information-assistant role.

### 1.2 Non-goals and safety boundary

The system is not designed to diagnose a patient, prescribe treatment, score clinical risk, or substitute for a qualified healthcare professional. PDF embeddings and retrieved document passages are not patient features or outcome labels. Any future patient-level prediction capability would require a distinct governed product, authorised structured data, defined outcomes, calibration, validation, and clinical oversight.

## 2. Users and core journeys

| User / context | Need | Successful outcome |
|---|---|---|
| Researcher, learner, or clinician using an approved document corpus | Locate relevant information in long medical PDFs | Receives a concise answer based on retrieved source context |
| Document curator or project operator | Add source material to the corpus | PDF text is extracted, chunked, embedded, and made retrievable |
| Project maintainer | Assess whether changes improve the system | Can inspect health, evaluation results, traces, metrics, and logged failures |

## 3. Functional requirements

### FR-01 — Accept documents through an API boundary

The backend shall accept one or more PDF uploads through `POST /upload_pdfs/`. It shall validate the request boundary and pass accepted files to the ingestion workflow. 

**Current implementation evidence.** The project documents PDF upload as the ingestion entry point and exposes an upload endpoint through FastAPI. The repository also contains typed request/response schemas and upload validation logic.

### FR-02 — Convert PDFs into retrievable chunks

The system shall extract raw text from uploaded PDFs and split it into smaller units that preserve useful context across chunk boundaries. The documented implementation uses `RecursiveCharacterTextSplitter`; the verified loader is configured with 500-character chunks and 100-character overlap. 

**Rationale.** Retrieval models operate on manageable passages rather than full documents. Overlap reduces the risk that a relevant fact is split exactly at a chunk boundary.

### FR-03 — Produce semantic representations and store them for search

The system shall embed document chunks using `all-mpnet-base-v2` and persist vectors in a semantic-search backend. The documented production vector store is Pinecone serverless; Qdrant is retained as a local-development alternative. 

**Rationale.** Dense semantic retrieval allows a question and source passage to match even where their wording differs.

### FR-04 — Retrieve source context for a user question

The system shall accept a natural-language question through `POST /ask/`, embed it, search the vector store, and provide the retrieved context to the answer-generation chain. The verified implementation requests the top three Pinecone matches. 

**Trade-off.** A bounded retrieval budget limits latency, token use, and irrelevant context. It may also omit useful qualifiers or return passages without enough surrounding context. The value of top-k, chunk size, and overlap must therefore be evaluated rather than treated as universal constants.

### FR-05 — Generate a readable answer from retrieved context

The system shall combine retrieved context with a system prompt in a RAG chain and use a language model to generate a concise, human-readable response. The documented stack uses LangChain orchestration and a Groq-hosted Llama model.  

**Rationale.** Retrieval supplies evidence; the LLM translates that evidence into an accessible response. The architecture does not assume that a fluent answer is automatically correct.

### FR-06 — Return a health signal and support deployability

The backend shall expose `GET /health` to report service status and dependency checks. The project documents containerised server/client services, Docker Compose orchestration, typed environment configuration, and CI/CD support.  

### FR-07 — Measure quality and operating behaviour

The system shall support quality evaluation and operational observability. The documented completed foundations include RAGAS metrics, a curated 51-pair medical Q&A set, a CI regression gate, LangSmith tracing, Prometheus metrics, PostgreSQL query logging, cost tracking, and Grafana dashboard configuration. 

**Boundary.** These signals are engineering and RAG-quality evidence. They are not proof of clinical validity, medical correctness, or safe patient-level decision making.

## 4. Quality attributes and constraints

| Quality attribute | Design requirement | Current evidence / limitation |
|---|---|---|
| Grounding | Keep source context external to the model and retrieve it before generation | RAG pipeline, vector store, and source-return path are documented. Retrieval can still be irrelevant or based on weak material. |
| Traceability | Make quality and operational failure visible | RAGAS, tracing, metrics, logging, and CI regression are documented. Source names alone are weaker than page/excerpt-level citation. |
| Reliability | Fail fast on missing configuration and expose service health | Pydantic Settings, health check, Docker/Compose, and CI are documented. Runtime resilience still needs tests and controlled failure handling. |
| Security & privacy | Protect untrusted input and sensitive information | Rate limiting is documented as completed. PII detection/redaction, prompt-injection control, retries, and full I/O validation remain Phase 4 work.  |
| Retrieval quality | Retrieve relevant passages efficiently | Dense retrieval is implemented. Hybrid search, query rewriting, reranking, metadata filtering, RAG-Fusion, and context management are documented as Phase 5 work.  |
| Clinical boundary | Avoid overclaiming and medical decision making | The project guide says it should not present itself as a doctor; this specification treats it as information assistance only.   |

## 5. Architecture specification

```text
                         ┌─────────────────────────────────┐
                         │          Streamlit client        │
                         │     upload PDFs / ask question   │
                         └───────────────┬─────────────────┘
                                         │
                         ┌───────────────▼─────────────────┐
                         │            FastAPI API           │
                         │ /upload_pdfs · /ask · /health    │
                         └───────┬───────────────────┬─────┘
                                 │                   │
                 ingestion path  │                   │  query path
                                 ▼                   ▼
              extract → split → embed        embed question → retrieve top-k
                                 │                   │
                                 ▼                   ▼
                       Pinecone vector store   retrieved source context
                                 │                   │
                                 └─────────┬─────────┘
                                           ▼
                        LangChain RAG chain + Groq / Llama
                                           ▼
                         readable response + source information

Supporting: Pydantic Settings · rate limiting · Docker/Compose · CI · RAGAS ·
LangSmith · Prometheus · PostgreSQL logging · Grafana
```

## 6. Design decisions and rationale

| Decision ID | Decision | Why it fits the requirement | Trade-off / next check |
|---|---|---|---|
| D-01 | Use RAG instead of a general, ungrounded chatbot | The document corpus remains explicit, replaceable, and retrievable. | Grounding is not factual proof; corpus governance and citation support must improve. |
| D-02 | Separate client and FastAPI service | Keeps the UI separate from the retrieval and generation service boundary. | Adds deployment and API-contract work. |
| D-03 | Use dense embeddings and a vector store | Supports semantic retrieval when question and document wording differ. | Dense-only retrieval can miss exact terms, metadata, negation, and document versions. |
| D-04 | Use top-k = 3 as a bounded default | Controls context size, latency, and cost in a prototype. | Must be tuned against a held-out evaluation set. |
| D-05 | Use hosted Groq/Llama and LangChain | Reduces prototype infrastructure burden and speeds iteration. | Introduces provider dependency, model/version change risk, and data-flow considerations. |
| D-06 | Add evaluation and observability foundations | AI failures span ingestion, retrieval, generation, latency, and infrastructure. | Automated RAG metrics need supplementation with curated relevance labels, citation tests, and expert review. |

## 7. Requirement-to-implementation traceability

| Requirement | Documented implementation / evidence | Status | Interview-safe statement |
|---|---|---|---|
| FR-01: PDF upload | FastAPI `/upload_pdfs/`, upload validation, PDF extraction | Implemented foundation | “The system has a dedicated document-ingestion path rather than treating files as chat context.” |
| FR-02: Chunk documents | `RecursiveCharacterTextSplitter`; 500-character chunks and 100-character overlap | Implemented foundation | “Chunking is a measurable retrieval choice, not an invisible preprocessing step.” |
| FR-03: Embed and index | `all-mpnet-base-v2`, Pinecone serverless; Qdrant local alternative | Implemented foundation | “I chose semantic retrieval to bridge wording differences, while recognising dense-only retrieval has limits.” |
| FR-04: Retrieve context | Query embedding and Pinecone top-k = 3 retrieval | Implemented foundation | “Top-k three is a latency/context default that should be evaluated rather than defended as optimal.” |
| FR-05: Grounded generation | LangChain RAG chain and Groq/Llama model | Implemented foundation | “The retrieved corpus is the knowledge boundary; the model should transform evidence, not replace it.” |
| FR-06: Health/deployment | Docker, Compose, typed settings, `/health`, CI/CD | Phase 1 documented completed | “Reproducibility and health checks are part of an AI service, not deployment polish.” |
| FR-07: Evaluation/observability | RAGAS, 51-pair dataset, CI gate, LangSmith, Prometheus, PostgreSQL, Grafana | Phases 2–3 documented completed | “Observability gives a feedback loop; it does not establish clinical validity.” |
| Phase 4 hardening | Caching, I/O validation, prompt-injection control, PII redaction, retry, async uploads | In progress | “These are explicit hardening targets, not implemented claims.” |
| Phase 5 RAG optimisation | Hybrid search, rewrite, rerank, A/B chunking, metadata filters, RAG-Fusion, context management | Not started | “I would evaluate these against a stable test set before adding them.” |
| Phase 6 QA/testing | Unit, integration, load, adversarial, regression, smoke tests | Not started | “The roadmap identifies the proof obligations needed before stronger deployment claims.” |

## 8. Acceptance criteria and deliberate limitations

The specification considers the core prototype requirement satisfied when a PDF can be uploaded, transformed into embeddings, retrieved in response to a question, and used by the RAG chain to generate a readable response. The production-foundation requirement is supported by documented health, containerisation, CI, evaluation, tracing, metrics, logging, and cost-tracking work.

The specification does **not** claim numerical accuracy, a target latency, medical safety, HIPAA/GDPR compliance, security certification, clinical validation, or successful patient-level prediction. Those claims require dedicated evidence and governance beyond the documented prototype and enhancement roadmap.