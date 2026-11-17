# RAG architecture and module boundaries

## Design

This project uses a modular-monolith architecture: one deployable application with clear responsibilities and replaceable boundaries. Each stage can be tested or replaced without turning the learning project into a collection of microservices.

## End-to-end flow

    DOCUMENT INGESTION
    Upload -> Extract -> Normalize -> Chunk -> Embed -> Vector Store
                                                       |
                                                       v
    QUESTION -> Query Embed -> Retrieve -> [Optional Rerank]
                                          -> Prompt Builder -> LLM -> Answer + Sources

    EVALUATION: labelled queries -> Precision@K / Recall@K / MRR / Hit Rate

## Module responsibilities

| Module | Responsibility |
|---|---|
| app/api/ | HTTP endpoints, request validation, and response status codes |
| app/schemas/ | Validated request and response data shapes |
| app/core/config.py | Environment-based configuration |
| app/core/database.py | PostgreSQL connection lifecycle and pgvector initialization |
| app/services/extractor.py | File-to-text extraction |
| app/services/chunker.py | Text splitting and overlap |
| app/services/embedder.py | Text-to-vector API adapter |
| app/services/vector_store.py | PostgreSQL/pgvector persistence and similarity search |
| app/services/ingestion.py | Coordinates extraction, chunking, embedding, and persistence |
| app/services/retriever.py | Embeds questions and retrieves scoped candidate chunks |
| app/services/reranker.py | Optional local lexical candidate reranking |
| app/services/prompt_builder.py | Builds grounded prompts and labels source text as reference data |
| app/services/generator.py | Calls the configured chat-completions provider |
| app/services/rag.py | Coordinates retrieval, reranking, and generation |
| app/services/evaluation.py | Offline retrieval-quality metrics |
| app/ports/ | Protocol contracts for replaceable pipeline components |
| tests/ | Unit and API contract tests |

## Dependency direction

API routes call application services. Ingestion and retrieval coordinate the pipeline. Provider-specific code lives in adapters such as the embedder and vector store. Ports define the expected behavior so adapters can be replaced without changing API request formats.

## Quality and safety notes

- Retrieved document text is reference data, not application policy.
- Answers should cite source passages and acknowledge when evidence is insufficient.
- Tenant and knowledge-base filters are applied to vector search.
- The lexical reranker is a simple deterministic baseline, not a learned cross-encoder; it is disabled by default.
- Evaluation helpers calculate metrics but require a representative labelled test dataset to produce meaningful quality measurements.
- The current deployment uses deployment-level tenant isolation, not independent customer identities and keys.

## Extending the system

A future provider can implement the relevant port and be wired through configuration. A learned reranker can replace the lexical baseline. A labelled evaluation dataset can be added to benchmark chunk sizes, embedding models, retrieval depth, and reranking.
