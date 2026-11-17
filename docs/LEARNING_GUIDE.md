# Beginner Learning Guide: every RAG stage explained

This guide is written so you can explain the project to someone who has never built an AI application.

## First: what problem are we solving?

Imagine you have 500 company PDFs. You ask an AI assistant: “What is our leave policy?” A general AI model may not know your company's policy. RAG gives the application a way to search those PDFs and find the relevant paragraphs before an AI model answers.

Think of RAG like an open-book exam:
- The documents are the textbook.
- Retrieval is finding the right pages.
- Generation is writing the answer using those pages.

## Stage 1 — Ingestion: receive the document

**Meaning:** ingestion is the process of bringing a document into the application.

**What happens:** the API receives a file, checks its type/size, and passes it to the processing pipeline.

**Why it matters:** the system needs a controlled entry point. Without ingestion, it has no document to learn from.

**Example:** upload `employee-handbook.pdf`.

**Project location:** `app/api/routes/documents.py` receives the upload; `app/services/ingestion.py` coordinates processing.

## Stage 2 — Extraction: read the document

**Meaning:** extraction converts a file into plain text that software can process.

**What happens:** PDF text is read from its pages; TXT and Markdown files are decoded as text.

**Why it matters:** an embedding model works with text, not with a PDF file object.

**Example:** a PDF page containing “Annual leave is 20 days” becomes a text string.

**Project location:** `app/services/extractor.py`.

**Limit:** scanned PDFs are images. They need OCR (Optical Character Recognition) before their text can be extracted. OCR is not currently included.

## Stage 3 — Chunking: divide text into useful pieces

**Meaning:** a chunk is a smaller section of the extracted text.

**What happens:** a long document is split into pieces of a configured size. Neighboring pieces overlap slightly.

**Why it matters:** sending an entire large document for every search is inefficient. Small passages make it easier to find the exact information. Overlap helps avoid losing meaning at a boundary.

**Example:** a 30-page handbook becomes many smaller passages instead of one giant block.

**Project location:** `app/services/chunker.py`. Settings: `CHUNK_SIZE` and `CHUNK_OVERLAP`.

## Stage 4 — Embedding: turn meaning into numbers

**Meaning:** an embedding is a list of numbers (a vector) produced by an embedding model.

**What happens:** each chunk is sent to the configured embedding provider. The provider returns a vector representing the text's semantic meaning.

**Why it matters:** a database can compare vectors to find passages that are conceptually close, even when the exact words differ.

**Example:** “How much vacation can staff take?” may be close in meaning to “Annual leave entitlement”.

**Project location:** `app/services/embedder.py`; provider contract: `app/ports/embeddings.py`.

**Important:** vectors produced by incompatible models or dimensions must not be mixed in the same index.

## Stage 5 — Storage: save chunks and vectors

**Meaning:** storage saves the chunk text and its vector so we can search it later.

**What happens:** the application stores the original passage, document ID, source filename, chunk position, metadata, and embedding vector.

**Why it matters:** without persistence, documents would have to be reprocessed every time the application restarts.

**Project location:** `app/core/database.py`; PostgreSQL uses the pgvector extension for vector data.

## Stage 6 — Query embedding: understand the question in vector form

**Meaning:** query embedding converts the user's question into a vector using the same embedding model used for document chunks.

**What happens:** the question is embedded before searching the vector database.

**Why it matters:** the question and stored passages must be represented in a compatible vector space to compare their meaning.

**Project location:** the retrieval flow calls the embedding component in `app/services/retriever.py`.

## Stage 7 — Retrieval: find the most relevant passages

**Meaning:** retrieval is searching for the stored chunks closest in meaning to the question.

**What happens:** pgvector compares the question vector with stored vectors and returns the best matches (top-k).

**Why it matters:** the answer should be based on relevant source material, not a guess.

**Example:** the question “How much vacation can staff take?” returns the chunk describing annual leave.

**Project location:** `app/services/retriever.py`.

## Stage 8 — Generation: write an answer (planned next stage)

**Meaning:** generation sends the question and retrieved passages to a language model (LLM), asking it to compose an answer grounded in that context.

**Why it matters:** retrieval finds evidence; generation turns that evidence into a readable response.

**Current status:** not implemented yet. The query endpoint returns matching chunks and similarity distances. Do not describe this repository as already generating answers.

## The complete flow in 30 seconds

“When someone uploads a file, we ingest it. We extract its text, split the text into chunks, convert each chunk into an embedding, and save the chunks and vectors in PostgreSQL with pgvector. When someone asks a question, we embed the question, search for similar vectors, and return the most relevant passages. A generation module can then use those passages to write a grounded answer.”

## Useful vocabulary

| Term | Plain-English meaning |
|---|---|
| RAG | Search your own knowledge before generating an AI answer |
| Chunk | A small piece of a larger document |
| Embedding | Numbers representing the meaning of text |
| Vector | A list of numbers |
| Vector database | A database that can search vectors by similarity |
| Similarity search | Finding items with meaning close to the query |
| Top-k | The number of best matches to return |
| LLM | Large Language Model; the AI that can write the final answer |
| OCR | Technology that reads text from images/scanned pages |
| API | A defined way for software systems to communicate |
| Contract/interface | A rule describing what a module must provide |
| Adapter | Code that connects an interface to a specific technology |
