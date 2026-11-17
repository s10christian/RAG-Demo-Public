# RAG Demo — presentation notes

## Slide 1: The problem

“We have documents, but a language model does not automatically know what is inside our private files. We need a way to search those files and bring the right information into the AI workflow.”

## Slide 2: The solution

“RAG stands for Retrieval-Augmented Generation. It retrieves relevant information from our own documents and can use that information to ground an AI-generated answer.”

## Slide 3: Preparing the knowledge

Explain the first five stages:
1. **Ingestion:** receive the file.
2. **Extraction:** read the text.
3. **Chunking:** divide the text into smaller passages.
4. **Embedding:** convert each passage into a vector (numbers representing meaning).
5. **Storage:** save passages and vectors for later search.

## Slide 4: Asking a question

Explain the next two stages:
6. **Query embedding:** convert the question into a vector.
7. **Retrieval:** find the stored passages whose vectors are closest to the question vector.

## Slide 5: Producing an answer

“Generation is the next stage. It gives the question and retrieved passages to a language model so it can write a grounded answer. This demo currently stops at retrieval and returns the matching passages.”

## Slide 6: Why modularity matters

“Each stage has one responsibility. If we change the PDF reader, we should not have to rewrite the embedding stage. If we change the embedding provider, we should not have to rewrite the API. Contracts describe what each component must do; adapters connect those contracts to specific technologies.”

## Demo sequence

1. Start the application with Docker Compose.
2. Open `/docs`.
3. Upload a small PDF, TXT, or Markdown file using the documents endpoint.
4. Ask a question about that file using the query endpoint.
5. Point out that the response contains matching passages, not a generated answer.

## Honest project limitations to mention

- Scanned-PDF OCR is not included.
- The generation/LLM-answer stage is not implemented.
- The project is a learning/demo foundation, not production-hardened.
- Provider and vector-store dependency injection is the next architecture improvement; the new ports document the boundaries, but existing code still has some direct wiring.
