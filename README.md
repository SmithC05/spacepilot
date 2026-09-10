# SpacePilot 🚀

> **Your workspace. On autopilot.**

SpacePilot is an AI-powered autonomous operations assistant for campuses, offices, and shared workspaces. It lets teams find rooms, navigate buildings, check policies, and manage bookings through a conversational AI interface.

---

## What SpacePilot Is

SpacePilot connects four independent services:

| Service | Purpose |
|---------|---------|
| **frontend** | Next.js chat UI — the user-facing interface |
| **backend** | FastAPI REST API + SQLite database |
| **mcp** | MCP tool server — exposes backend tools to the AI agent |
| **agent** | AI reasoning loop (Amazon Bedrock + Strands Agents) |

---

## Required Software

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| npm | 9+ (included with Node.js) |

AWS credentials are only needed when the Bedrock/agent functionality is enabled. The app runs fully without AWS for frontend + backend development.

---

## Running the Services

### 1. Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs at **http://localhost:3000**

Copy the example env file before first run:

```bash
copy .env.example .env.local    # Windows
```

---

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Runs at **http://localhost:8000**

API docs (Swagger): http://localhost:8000/docs

> **The SQLite database is created automatically when the backend starts.**
> No migration command is required. The file `backend/data/spacepilot.db`
> is created on first launch. In production, change `DATABASE_URL` to a
> PostgreSQL URL — no code changes needed.

Copy the example env file before first run:

```bash
copy .env.example .env    # Windows
```

---

### 3. MCP Server

```bash
cd mcp
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

The MCP server exposes SpacePilot tools to the AI agent. It must be running when the agent service is active.

---

### 4. Agent

```bash
cd agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python agent.py
```

The agent currently returns a placeholder response. The AI team will connect it to Amazon Bedrock (Claude via Strands Agents).

AWS credentials are required only when Bedrock calls are actually enabled:

```bash
copy .env.example .env    # Windows
# then fill in AWS_REGION and BEDROCK_MODEL_ID in .env
```

---

## Virtual Environments

Use a **separate virtual environment for each Python service** to avoid package version conflicts (FastAPI and the MCP SDK require different versions of Starlette).

```
backend/.venv
mcp/.venv
agent/.venv
```

Activate on Windows:

```bash
.venv\Scripts\activate
```

Activate on macOS/Linux:

```bash
source .venv/bin/activate
```

---

## Project Structure

```
spacepilot/
├── frontend/                # Next.js + TypeScript + Tailwind
│   ├── app/
│   │   ├── page.tsx         # Main chat interface
│   │   ├── layout.tsx       # Root layout + font
│   │   └── globals.css      # Design system (tokens, classes, animations)
│   └── components/          # Reusable UI components
│       ├── Button.tsx
│       ├── Card.tsx
│       ├── Input.tsx
│       ├── ChatMessage.tsx
│       ├── AgentStatus.tsx
│       └── LoadingIndicator.tsx
│
├── backend/                 # FastAPI + SQLAlchemy + SQLite
│   ├── app/
│   │   ├── main.py          # FastAPI app entry point
│   │   ├── database.py      # DB engine (SQLite dev → PostgreSQL prod)
│   │   ├── models.py        # SQLAlchemy ORM models
│   │   ├── schemas.py       # Pydantic request/response schemas
│   │   └── routes/          # One file per route group
│   └── data/                # spacepilot.db lives here (auto-created)
│
├── mcp/                     # MCP tool server
│   ├── server.py            # FastMCP server + tool registration
│   └── tools.py             # Tool implementations (call backend API)
│
├── agent/                   # AI agent service
│   ├── agent.py             # process_request() — implement here
│   └── prompts.py           # System prompt + few-shot examples
│
├── README.md
└── .gitignore
```

---

## Team Split

| Area | Folder | Tasks |
|------|--------|-------|
| Frontend | `frontend/` | Chat UI, room list, booking form, map |
| Backend | `backend/` | API routes, models, availability logic |
| MCP | `mcp/` | Tool implementations, backend integration |
| Agent | `agent/` | Strands agent, Bedrock prompts, reasoning |

---

## Environment Variables

| Service | File | Key Variables |
|---------|------|---------------|
| Frontend | `frontend/.env.local` | `NEXT_PUBLIC_BACKEND_URL` |
| Backend | `backend/.env` | `DATABASE_URL`, `API_PORT` |
| MCP | `mcp/.env` | `BACKEND_URL` |
| Agent | `agent/.env` | `AWS_REGION`, `BEDROCK_MODEL_ID` |

Each service has a `.env.example` file — copy it and fill in your values.
**Never commit `.env` files** — they are in `.gitignore`.
