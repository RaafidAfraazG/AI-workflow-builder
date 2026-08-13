# AI Workflow Builder

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%2B-336791?logo=postgresql&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5.23-FF6B35)
![License](https://img.shields.io/badge/license-MIT-green)

A visual Agentic AI workflow platform for designing and executing multi-step AI pipelines without writing code. It combines document intelligence, semantic retrieval, configurable LLMs, and workflow orchestration through an interactive drag-and-drop interface.

---
## 🎥 Demo (Click To Open)

<a href="https://www.loom.com/share/4175ff7a7e5647749622cd305c39d6ec" target="_blank">
  <img width="960" height="499" alt="AI Workflow Builder Demo" src="https://github.com/user-attachments/assets/9e2b1ba4-0d15-49b7-b4ea-9da304b0ff47" />
</a>

---

## Features

- **Visual graph editor** — drag, drop, and connect AI nodes on a React Flow canvas
- **Built-in AI nodes**: User Query, Knowledge Base (RAG), LLM Engine, Output
- **PDF knowledge base** — upload → PyMuPDF text extraction → overlap-chunked embedding → ChromaDB per-workflow collections
- **Agentic orchestration** — `WorkflowOrchestrator` traverses the edge graph, executes each node in sequence, and accumulates context across stages
- **Real-time LLM streaming** — Server-Sent Events (SSE) deliver token-by-token responses to the UI
- **Dual LLM + embedding support** — Google Gemini (`gemini-2.5-flash`, `gemini-embedding-001`) and OpenAI (`gpt-3.5-turbo`, `text-embedding-ada-002`), plus a mock provider for local development
- **Per-node configuration** — custom prompt templates, top-K retrieval, output format (`text` / `json` / `markdown`)
- **Chat session management** — full CRUD: create, rename, delete, and switch named sessions per workflow
- **REST API + Swagger UI** — FastAPI auto-generates interactive docs at `/docs`; Alembic manages schema migrations

---
## Highlights

- Visual AI workflow orchestration
- Retrieval-Augmented Generation (RAG)
- Semantic search using vector embeddings
- Multi-LLM support (Gemini & OpenAI)
- Streaming AI responses (SSE)
- Modular workflow execution engine
- Persistent workflow and chat management


## Architecture

```
┌──────────────────────────────────────────┐
│  Browser  ·  React 18 + Vite            │
│  React Flow  ·  Zustand  ·  TanStack Query│
│  Tailwind CSS  ·  Shadcn UI  ·  Port 5173 │
└─────────────────┬────────────────────────┘
                  │  REST + SSE
┌─────────────────▼────────────────────────┐
│            FastAPI                       │
│  /api/workflows  /api/kb  /api/health    │
│  WorkflowOrchestrator (graph runner)     │
└──────────┬───────────────────────────────┘
           │
     ┌─────┴──────┐      ┌───────────────────┐
     │ PostgreSQL  │      │ ChromaDB (embedded)│
     │             │      │  ./chroma_data     │
     └────────────┘      └───────────────────┘
```

**Execution path**: `userQuery → knowledgeBase → llmEngine → output`

The orchestrator follows directed edges saved in PostgreSQL, runs each node, builds a shared context object (KB results → prompt → LLM response), and streams the final answer over SSE.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, TypeScript, React Flow 11 |
| State / Data | Zustand, TanStack Query v4 |
| UI | Shadcn UI, Radix UI, Tailwind CSS 3, Lucide Icons |
| Backend | FastAPI 0.115, Uvicorn, Python 3.11 |
| ORM / DB | SQLAlchemy 2.0, Alembic, PostgreSQL 16+ |
| Vector store | ChromaDB 0.5.23 (embedded persistent) |
| PDF extraction | PyMuPDF (fitz) |
| LLM / Embeddings | `google-genai` (Gemini), `openai` SDK |
| Config / Testing | Pydantic Settings v2, pytest, pytest-asyncio, httpx |

---

## Project Structure

```
ai-workflow-builder/
├── backend/
│   ├── app/
│   │   ├── api/            # Route handlers: workflows, kb, health
│   │   ├── core/           # Config (Pydantic Settings), DB engine
│   │   ├── models/         # SQLAlchemy ORM: Workflow, Node, Edge, Chat, Message, Document
│   │   ├── runners/        # WorkflowOrchestrator — graph execution engine
│   │   ├── services/       # LLMService, EmbeddingService, KnowledgeBaseService
│   │   ├── schemas/        # Pydantic request / response schemas
│   │   ├── utils/          # PromptBuilder
│   │   └── main.py
│   ├── alembic/            # Database migrations
│   ├── tests/              # pytest unit tests (graph validation, KB search)
│   ├── e2e_test.py         # End-to-end API test script
│   └── .env.example
│
└── frontend/
    └── src/
        ├── components/
        │   ├── builder/    # BuilderPage, WorkflowCanvas, NodePalette,
        │   │               # ConfigPanel, TopBar, ChatWindow
        │   ├── nodes/      # UserQueryNode, KnowledgeBaseNode,
        │   │               # LlmEngineNode, OutputNode
        │   └── WorkflowList.tsx
        ├── lib/            # api.ts (typed client + SSE), types.ts
        └── store/          # builderStore.ts (Zustand)
```

---

## Quick Start

**Prerequisites:** Python 3.11, Node.js 18+, PostgreSQL 16+ (database named `workflow_builder`)

> **Note (Windows):** ChromaDB 0.5.x requires Python 3.11. Pre-built wheels are unavailable for 3.12+ without C++ Build Tools.

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # set DATABASE_URL and an LLM API key
alembic upgrade head
python -m uvicorn app.main:app --reload
```

API → `http://localhost:8000` · Swagger UI → `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install && npm run dev
```

App → `http://localhost:5173`

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env`:

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:password@localhost:5432/workflow_builder` |
| `LLM_PROVIDER` | `gemini` \| `openai` \| `mock` | `mock` |
| `GEMINI_API_KEY` | Required when using Gemini | — |
| `GEMINI_MODEL` | Gemini chat model | `gemini-2.5-flash` |
| `GEMINI_EMBEDDING_MODEL` | Gemini embedding model | `gemini-embedding-001` |
| `OPENAI_API_KEY` | Required when using OpenAI | — |
| `EMBEDDING_PROVIDER` | Auto-inherits `LLM_PROVIDER` if unset | `mock` |
| `CHROMA_PERSIST_DIR` | ChromaDB storage path | `./chroma_data` |
| `CORS_ORIGINS` | Allowed origins (JSON array) | `["http://localhost:5173"]` |

> Get a Gemini API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

---

## Testing

```bash
# Unit tests
cd backend && pytest tests/

# End-to-end (requires a running server and at least one LLM key configured)
cd backend && python e2e_test.py
```

The E2E script covers: workflow creation → PDF upload → ChromaDB ingestion → build validation → chat session → SSE message stream → response assertion.

