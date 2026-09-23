# Enterprise AI Assistant

A workspace-based knowledge assistant prototype for teams that want to upload internal documents and ask questions with retrieved sources.

## Problem

Answers to internal questions are spread across files. This project extracts their text, indexes it for semantic search and passes matching passages to an answer model. Users can inspect the returned document names, relevance scores and text previews.

## Stack

- Python 3.11, FastAPI, Pydantic and raw `psycopg2` database access.
- Next.js 16, React 19 and TypeScript in `frontend/`.
- PostgreSQL 15 for users, workspaces, settings, document records and conversations.
- Sentence Transformers with local `BAAI/bge-m3` embeddings; persistent ChromaDB for vector search.
- OpenAI for answer generation, JWT authentication, bcrypt, Docker Compose and pytest.

## Architecture

```text
Next.js interface --> FastAPI --> PostgreSQL application records
                         |
Upload --> file reader --> text chunks --> local embeddings --> ChromaDB
Question --> local embedding --> workspace collection --> retrieved passages
                                                              |
                                                         OpenAI answer
                                                              |
                                                   answer + source metadata
```

`app/services/` handles extraction, indexing, retrieval and document lifecycle operations. Each workspace gets a Chroma collection and a directory under `storage/workspaces/`. API routes check workspace access. Files, processed text, vectors and model downloads stay under `storage/` by default; relational records are in PostgreSQL.

Embeddings run locally. Questions and retrieved passages are sent to OpenAI for generation. The current answer path does not send saved conversation history to the model.

## Run locally

Use Docker with Compose v2 and Linux containers. The images provide Python 3.11 and Node.js 22. You need an OpenAI API key with access to your selected model, network access to download the embedding model, and free ports 3000, 8000 and 5432. The model and Python dependencies make the initial download substantial.

```sh
git clone https://github.com/ouastihamza/enterprise-ai-assistant.git
cd enterprise-ai-assistant
cp .env.example .env
openssl rand -hex 32
```

Set `JWT_SECRET_KEY` to the generated value and fill in `OPENAI_API_KEY` in `.env`. Keep the other database defaults for the supplied Compose setup. Do not commit `.env`.

| Variable | Purpose / default |
| --- | --- |
| `OPENAI_API_KEY` | A nonempty value is needed to initialize the client; a valid key is needed for real answers. |
| `JWT_SECRET_KEY` | Required token signing secret. |
| `OPENAI_MODEL`, `TEMPERATURE` | Shared client defaults: `gpt-5.5`, `0.2`. Workspace settings select the model and temperature used by chat. |
| `JWT_ALGORITHM` | `HS256`. |
| `DB_HOST`, `DB_PORT` | `db`, `5432`; Compose overrides the host to `db`. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Local development defaults matching the Compose database service. |
| `DATABASE_URL` | Optional full connection string; overrides the individual database fields. Omit for the standard setup. |
| `VECTOR_DB_PATH` | Optional path; omit to use `storage/vector_db`. Do not set it to an empty value. |
| `HF_HOME` | Optional embedding-model cache location; defaults to `storage/huggingface`. |
| `NEXT_PUBLIC_API_BASE_URL` | Browser-visible API URL, set to `http://localhost:8000` as a frontend build argument in Compose. |

```sh
docker compose up --build
```

Open `http://localhost:3000/register`, create an account, select or create a workspace, and upload a text document from Knowledge. Then open Assistant and ask about that document. API documentation is at `http://localhost:8000/docs`.

The Compose database uses a named volume; API files use the `./storage` bind mount. Services create their database tables on startup. The committed database password is a local development default, not a production credential.

### Fictional customer demo

After signing in, open **Customers** and choose **Prepare demo customer**. The idempotent seed action creates the fictional **Demo Industrie SAS** profile, three sites, and four clearly marked fictional documents. The documents pass through the normal ingestion and indexing pipeline.

Open the customer profile, then open **Assistant** (the demo customer is selected automatically) and ask:

> Why was February more expensive than January?

With a valid `OPENAI_API_KEY`, the assistant combines the structured customer profile with the January invoice, February invoice, contract, and consumption documents and returns a grounded response with sources. No real customer or SEFE data is included.

Customer routes live under `/workspaces/{workspace_id}/customers`: list, create, `seed-demo`, get one customer, and add a site. Document uploads accept optional `customer_id` and `category` fields.

For frontend development outside Docker, install Node.js 22 and npm, start the backend with `docker compose up --build db api`, then in another terminal run:

```sh
cp frontend/.env.example frontend/.env.local
npm --prefix frontend ci
npm --prefix frontend run dev
```

### Tests

The pytest suite exercises authentication, document upload/deletion, workspace access and retrieval. It uses real PostgreSQL, ChromaDB and local embeddings; answer calls are mocked. Run it against disposable local data. The Docker build excludes tests, so mount them explicitly:

```sh
docker compose up -d db
docker compose build api
docker compose run --rm -e OPENAI_API_KEY=test-placeholder -v "$PWD/tests:/app/tests:ro" api python -m pytest -q
```

The first retrieval test can download the embedding model. Native macOS Python installation is not covered by the locked requirements, which pin a Linux CPU Torch wheel. Frontend checks are `npm --prefix frontend run lint` and `npm --prefix frontend run build` after installation.

## Implementation status

- Implemented in `main`: registration/login, workspace access checks, upload/list/delete routes, local embedding and indexing, similarity filtering, answers with source metadata, saved conversations and workspace settings.
- Added on this branch: workspace-scoped customer profiles and sites, optional customer/category metadata on documents, and customer-aware assistant context that combines PostgreSQL records with indexed documents.
- Readers exist for PDF, DOCX, TXT, Markdown, CSV, XLSX, HTML, JSON, XML and PPTX. PDF extraction requires a text layer; there is no OCR pipeline.
- Not implemented in `main`: streamed answers, hybrid keyword/vector retrieval, model use of conversation history, or automated checks that generated citations match their claims.

Screenshot placeholder: capture the Assistant page with a question about a sample document, its answer and the expanded Sources panel. Keep the active workspace visible and use non-confidential sample content.

## Known limitations

- This is a prototype. End-to-end model behavior and the integration tests have not been verified for this documentation pass.
- Ingestion and model calls are synchronous. A first model download or long request can exceed the frontend's 30-second timeout.
- Returned sources describe retrieved chunks; some can be omitted from the model context by its size budget. Citations are prompted, not independently validated.
- Local files and Chroma storage need backup alongside PostgreSQL. There is no versioned database migration framework or distributed job queue.
- Defaults target local development, including database credentials, HTTP origins and browser token storage. Changing the embedding model or an existing collection's distance metric requires rebuilding its index.
- Experimental branches are separate from the default-branch application documented here.

## License

[MIT](LICENSE).
