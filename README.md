# AI Agency

AI Agency is a full-stack internal knowledge assistant platform that lets teams upload company documents, process them into a searchable knowledge base, and ask questions grounded in their content. The project combines a FastAPI backend, a Next.js frontend, PostgreSQL persistence, ChromaDB vector search, and a modular document-processing pipeline.

It is designed for organizations that want a self-hosted, workspace-aware AI assistant for internal documents without depending on a fully managed SaaS solution.

## What this project does

AI Agency provides an end-to-end workflow for creating an internal knowledge assistant:

- create and manage isolated workspaces for teams or companies
- upload documents in multiple formats
- extract and normalize text from files
- split content into chunks for retrieval
- generate embeddings and index them in ChromaDB
- perform semantic search for relevant context
- answer questions with RAG-style grounded responses
- expose the experience through a Next.js UI backed by a FastAPI API

## Core features

- Workspace-based isolation for different clients or teams
- Multi-format document ingestion for PDF, DOCX, TXT, Markdown, CSV, XLSX, HTML, JSON, XML, and PPTX files
- JWT-based authentication with secure user registration and login
- PostgreSQL-backed storage for users, workspaces, workspace settings, documents, and conversations
- Workspace settings for assistant naming, welcome messages, file-type rules, and model configuration
- Document upload, indexing, and deletion workflows
- Dashboard, Knowledge, AI Assistant, and Settings pages in the Next.js frontend
- Docker support for local deployment and development

## Architecture overview

The application follows a modular service-oriented design:

- Frontend: Next.js (React 19) UI under `frontend/`
- Backend: FastAPI API for authentication, workspace operations, workspace settings, documents, conversations, and the AI assistant
- Services: reusable modules for document processing, chunking, embedding, indexing, vector search, and RAG
- Storage: workspace-specific files and processed artifacts stored on disk under `storage/`
- Vector database: ChromaDB for semantic retrieval, one collection per workspace
- Database: PostgreSQL for all application state (users, workspaces, workspace settings, documents, conversations) — there is no ORM or migration tool; each service creates its own table with `CREATE TABLE IF NOT EXISTS` on startup

A typical workflow looks like this:

1. A user registers or signs in.
2. A workspace is created (a first-time user with no workspace gets one auto-created).
3. Documents are uploaded into the workspace.
4. The files are parsed and cleaned.
5. Text is chunked and embedded (locally, via `sentence-transformers`).
6. The vectors are indexed into ChromaDB.
7. The user asks a question and receives an answer grounded in retrieved context, with cited sources.

## Tech stack

**Backend**
- Python 3.11+
- FastAPI, uvicorn
- PostgreSQL 15 (raw `psycopg2`, no ORM)
- ChromaDB
- Sentence Transformers (`BAAI/bge-m3`, run locally)
- OpenAI (`gpt-5.5` by default)
- JWT authentication (`python-jose`, HS256), `bcrypt` password hashing

**Frontend**
- Next.js 16, React 19
- axios, framer-motion, lucide-react, react-markdown

**Infra**
- Docker / Docker Compose

## Repository structure

```text
AI-agency/
├── app/
│   ├── auth/                      # registration, login, JWT, user model/service
│   ├── configuration/             # per-workspace settings (chunk size, model, etc.)
│   ├── conversation/               # conversation + message persistence
│   ├── workspaces/                 # workspace model, service, routes
│   ├── api/                        # document, assistant, conversation routes
│   ├── services/                   # document processing, chunking, embedding,
│   │                                # indexing, vector search, RAG, file readers
│   ├── config.py                   # env var loading
│   ├── main.py                     # FastAPI app + router wiring
│   ├── llm_client.py                # shared OpenAI call wrapper
│   └── prompts.py
├── frontend/                       # Next.js app (App Router)
├── scripts/                        # process_document.py: the ingestion pipeline entrypoint
├── storage/                        # per-workspace files, chunks, and the Chroma DB (gitignored)
├── tests/                          # pytest suite (see Testing below)
├── docker-compose.yml
├── Dockerfile                      # backend image
├── frontend/Dockerfile             # frontend image
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.11 or newer
- Node.js 20+ and npm (for the frontend)
- pip
- Docker Desktop and Docker Compose (recommended for local development)
- An OpenAI API key (the app boots and most features work without one; only LLM answer generation needs a real key — see below)

## Environment configuration

Copy `.env.example` to `.env` in the project root and fill it in:

```bash
cp .env.example .env
```

```env
# --- OpenAI ---
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5.5
TEMPERATURE=0.2

# --- Auth ---
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=replace_with_a_random_hex_string
JWT_ALGORITHM=HS256

# --- PostgreSQL ---
# Defaults below match docker-compose.yml's db service. If you run the
# API outside Docker against that same container, set DB_HOST=localhost.
DB_HOST=db
DB_PORT=5432
DB_NAME=ai_agency
DB_USER=ai_user
DB_PASSWORD=ai_secure_password

# --- Vector store ---
# Defaults to <project_root>/storage/vector_db if unset.
VECTOR_DB_PATH=
```

The app boots without a real `OPENAI_API_KEY` — a missing or invalid key only surfaces when you actually ask the assistant a question (it returns a clear "Authentication failed" message instead of crashing). Everything else — auth, workspaces, document upload/indexing, vector retrieval, citations — works independently of OpenAI.

For the frontend, copy `frontend/.env.example` to `frontend/.env.local`:

```bash
cp frontend/.env.example frontend/.env.local
```

`NEXT_PUBLIC_API_BASE_URL` must be a URL reachable from the browser (e.g. `http://localhost:8000`), not a Docker-internal hostname — it gets baked into the client-side JS bundle at build time.

## Installation

```bash
git clone <your-repo-url>
cd AI-agency-
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd frontend
npm install
cd ..
```

## Running everything locally (without Docker)

You need Postgres running somewhere reachable. The simplest way is to start just the `db` service from Docker Compose and run the API and frontend directly:

```bash
docker compose up -d db
```

Then, in separate terminals:

```bash
# Terminal 1: backend
source .venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2: frontend
cd frontend
npm run dev
```

- API: http://localhost:8000
- Frontend: http://localhost:3000

## Running with Docker Compose (full stack)

```bash
docker compose up --build
```

This starts:

- PostgreSQL on port 5432
- the FastAPI API on port 8000
- the Next.js frontend on port 3000

The `frontend` service builds `frontend/Dockerfile` with `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` baked in at build time (see `docker-compose.yml`) so the browser can reach the API. If you deploy this somewhere other than localhost, update that build arg to the API's public URL and rebuild.

## API overview

### Authentication (`/auth`)

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `PATCH /auth/users/{user_id}/workspaces/{workspace_id}`

### Workspaces (`/workspaces`)

- `POST /workspaces/`
- `GET /workspaces/`
- `GET /workspaces/{workspace_id}`
- `PUT /workspaces/{workspace_id}`
- `PATCH /workspaces/{workspace_id}/archive`

### Workspace settings (`/workspace/settings`)

- `GET /workspace/settings?workspace_id=...`
- `PUT /workspace/settings`

### Documents (`/workspaces/{workspace_id}/documents`)

- `GET /workspaces/{workspace_id}/documents`
- `POST /workspaces/{workspace_id}/documents` (multipart file upload)
- `DELETE /workspaces/{workspace_id}/documents/{document_id}`

### AI Assistant (`/assistant`)

- `POST /assistant/chat`

### Conversations (`/conversations`)

- `GET /conversations?workspace_id=...`
- `POST /conversations`
- `GET /conversations/{conversation_id}`
- `PATCH /conversations/{conversation_id}`
- `DELETE /conversations/{conversation_id}`

## Usage flow

1. Start the backend and frontend (see above).
2. Register a new account at `/register`, or sign in at `/login`.
3. A default workspace is created automatically for a brand-new account.
4. Upload documents from the Knowledge page.
5. Wait for processing and indexing to complete.
6. Ask questions about the uploaded knowledge from the Assistant page.

## Testing

```bash
docker compose up -d db   # tests hit the real Postgres container
pytest
```

The suite (`tests/`) covers authentication, workspace isolation/authorization, document upload/deletion, and the assistant/RAG chat endpoint (with the OpenAI call mocked). It exercises the real FastAPI app, the real Postgres container, and the real local embedding model/ChromaDB — there's no test-double database, matching the rest of the codebase's raw-SQL, no-ORM design.

## Current status

- Auth, workspace management/isolation, document upload/indexing/deletion, RAG retrieval with citations, and conversation history all work end-to-end and are covered by tests.
- Next.js is the only frontend; the previous Streamlit frontend has been removed.
- All application state lives in PostgreSQL (users, workspaces, workspace settings, documents, conversations) — no JSON-file storage remains.

## Known technical debt

- No database migration tool: each service creates its table with `CREATE TABLE IF NOT EXISTS` on startup. Fine for the current scale; will need a real migration tool (e.g. Alembic) before schema changes become routine.
- `frontend/package.json` pins `next` and a few other packages to exact versions rather than ranges; `npm audit` currently reports vulnerabilities in `next` and some transitive dependencies that a version bump would fix, but doing so needs `--force` due to the exact pin — left as-is to avoid an unreviewed breaking upgrade during this cleanup pass.
- `requirements.txt` includes some large transitive packages (e.g. `pandas`, `pyarrow`, `kubernetes`, `GitPython`) that don't appear to be used directly by any remaining code; they weren't removed since a `pip freeze`-style requirements file makes "unused" hard to verify with full confidence, but they're worth auditing before a production deploy.

## License

This project is currently distributed as an internal/local project template. Adjust the license as needed for your environment.

## Maintainers

Maintained by the project contributors.
