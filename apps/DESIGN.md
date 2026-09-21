# AI PM Skills - Web UI Design

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser / Mobile                        │
│              Next.js 14 App Router (TypeScript)                 │
│         Tailwind + Shadcn/ui + Zustand + React Query            │
└────────────────┬────────────────────────────────────────────────┘
                 │  REST + SSE (streaming)
┌────────────────▼────────────────────────────────────────────────┐
│                     FastAPI Backend (Python)                    │
│              Reuses bot/agent.py directly                       │
│         SQLite (dev) / PostgreSQL (prod) for user data          │
└────────┬──────────────────────────────────────────┬────────────┘
         │                                          │
┌────────▼────────┐                    ┌────────────▼────────────┐
│  AI Providers   │                    │   File System           │
│  Anthropic      │                    │   my-projects/          │
│  Groq           │                    │   _system/              │
│  Gemini         │                    │   (same workspace as    │
│  OpenAI         │                    │    Telegram bot)        │
│  Ollama         │                    └─────────────────────────┘
└─────────────────┘
```

**Key insight:** The FastAPI backend reads/writes the same workspace files as the Telegram bot.
A PM can start on Telegram and continue on the web — everything is in sync automatically.

---

## Tech Stack

### Frontend
| Layer | Technology | Reason |
|-------|-----------|--------|
| Framework | Next.js 14 App Router | SSR/SSG for SEO, server components |
| Language | TypeScript | Type safety |
| Styling | Tailwind CSS | Same as GoClaw, utility-first |
| Components | Shadcn/ui | Accessible, customizable |
| State | Zustand | Lightweight, like GoClaw |
| Data fetching | TanStack Query | Caching, refetching |
| Forms | React Hook Form + Zod | Same as GoClaw |
| Markdown | react-markdown + remark-gfm | Render PM documents |
| Diagrams | Mermaid | PRD/architecture diagrams |
| Real-time | EventSource (SSE) | Streaming AI responses |
| i18n | next-i18next | EN/VI/ZH/FR/JA/ES |
| Icons | Lucide React | Same as GoClaw |

### Backend
| Layer | Technology | Reason |
|-------|-----------|--------|
| Framework | FastAPI | Python, reuses agent.py directly |
| Database | SQLite -> PostgreSQL | User accounts, API keys, sessions |
| Auth | JWT + bcrypt | Simple, secure |
| Streaming | SSE (Server-Sent Events) | AI response streaming |
| File ops | Pathlib | Workspace file management |
| AI agent | bot/agent.py (reused) | Zero code duplication |

### Infrastructure
| Component | Technology |
|-----------|-----------|
| Frontend build | Next.js standalone |
| Backend | uvicorn |
| Proxy | Nginx |
| Container | Docker Compose |
| CI/CD | GitHub Actions |

---

## Page Structure

```
/ (Dashboard)
  /setup                 <- First run: workspace + API key setup
  /chat                  <- AI conversation (main interface)
  /projects              <- All projects list
  /projects/[id]         <- Project dashboard
  /projects/[id]/discovery  <- FR, RICE, Research, Gate
  /projects/[id]/prd        <- PRD list + versions + Epics
  /projects/[id]/cr         <- Change requests workflow
  /projects/[id]/stakeholders <- Profiles + feedback log
  /settings              <- API keys, providers, workspace path
  /settings/providers    <- Configure AI providers
  /settings/team         <- Team members (future)
```

---

## Screen Designs

### Chat Interface (main)
```
┌─────────────────────────────────────────────────────┐
│ [Sidebar: Projects + Nav]  │  [Chat Area]           │
│                            │                        │
│ PROJ-001 AI Alignment      │ ┌────────────────────┐ │
│ PROJ-002 Checkout          │ │ User: Create FR... │ │
│                            │ └────────────────────┘ │
│ ─────────────              │ ┌────────────────────┐ │
│ Discovery                  │ │ AI: Got it. I'll   │ │
│ PRD                        │ │ capture this FR... │ │
│ Epics                      │ │                    │ │
│ CR                         │ │ [View FR-001] btn  │ │
│ Stakeholders               │ └────────────────────┘ │
│                            │                        │
│ ─────────────              │ ┌─────────────────────┐│
│ Settings                   │ │ Type a message...   ││
│                            │ └─────────────────────┘│
└─────────────────────────────────────────────────────┘
```

### Project Dashboard
```
┌─────────────────────────────────────────────────────┐
│ PROJ-001 - AI Alignment                [Open Chat]  │
│ Status: Active  Priority: P0  PM: [name]            │
│ ─────────────────────────────────────────────────── │
│                                                     │
│  Discovery      PRDs       Epics      CRs           │
│  FR: 3 total   PRD: 2     EP: 5      CR: 1 open    │
│  Gate: 2 pass  1 draft    3 approved  0 pending     │
│                                                     │
│ Milestones                                          │
│  M1 Discovery  [Done    ]  ████████████ 100%        │
│  M2 PRDs       [In Prog ]  ██████░░░░░░  60%        │
│  M3 Design     [Pending ]  ░░░░░░░░░░░░   0%        │
│                                                     │
│ Risks (2 open)                                      │
│  ! API timeline risk - raised by [Name]             │
└─────────────────────────────────────────────────────┘
```

### Settings / API Keys
```
┌─────────────────────────────────────────────────────┐
│ AI Provider Settings                                │
│ ─────────────────────────────────────────────────── │
│                                                     │
│ ☆ Anthropic Claude (Recommended)                   │
│   API Key: [sk-ant-...        ] [Test] [Save]       │
│   Model: claude-sonnet-4-6 ▼                        │
│   Status: ● Connected                               │
│                                                     │
│ Groq (Free tier)                                    │
│   API Key: [gsk_...           ] [Test] [Save]       │
│   Model: llama-3.3-70b-versatile ▼                  │
│   Status: ○ Not configured                          │
│                                                     │
│ Active Provider: [Anthropic Claude ▼]               │
└─────────────────────────────────────────────────────┘
```

---

## API Design

### Chat
```
POST /api/chat/stream          <- SSE streaming response
POST /api/chat/reset           <- Clear conversation history
GET  /api/chat/history         <- Get history for chat_id

Request:
{
  "message": "Create a feature request for dark mode",
  "project_id": "PROJ-001-ai-alignment"
}

SSE Response stream:
data: {"type": "text_delta", "text": "Got it. Let me"}
data: {"type": "text_delta", "text": " capture this..."}
data: {"type": "tool_use", "name": "write_file", "path": "..."}
data: {"type": "done", "suggestions": ["Score FR-001 with RICE", ...]}
```

### Projects
```
GET    /api/projects                    <- List all projects
GET    /api/projects/{id}              <- Project details
GET    /api/projects/{id}/documents    <- All docs in project
GET    /api/projects/{id}/discovery    <- FR + RICE + Research
GET    /api/projects/{id}/prd          <- PRD list with versions
GET    /api/projects/{id}/cr           <- CR workflow
GET    /api/projects/{id}/stakeholders <- Stakeholder profiles
GET    /api/projects/{id}/health       <- Health check
```

### Settings
```
GET  /api/settings/providers     <- List configured providers
POST /api/settings/providers     <- Save provider API key
POST /api/settings/providers/test <- Test connection
GET  /api/settings/workspace     <- Workspace path + status
POST /api/settings/workspace     <- Set workspace path
```

---

## SEO Strategy

Next.js App Router with:
- `generateMetadata()` for each page with title, description, OG tags
- `robots.txt` and `sitemap.xml`
- Structured data (JSON-LD) on landing page
- Static pages rendered server-side
- OpenGraph image generation for projects

```tsx
// app/layout.tsx
export const metadata: Metadata = {
  title: "AI PM Skills - AI Co-pilot for Product Managers",
  description: "Score features, write PRDs, manage Epics. Plain language. Files you own.",
  openGraph: { ... },
  twitter: { card: "summary_large_image", ... }
}
```

---

## Mobile Layout

Desktop: sidebar + main content
Mobile: bottom tab bar + full-screen pages

```
Mobile bottom bar:
[Chat] [Projects] [Settings]
```

---

## Implementation Phases

### Phase 1 — Foundation (2 weeks)
- FastAPI backend with SSE streaming chat
- Next.js project setup + Tailwind + Shadcn
- Chat page: send message, receive streaming response
- Settings page: save API keys, select provider
- Docker Compose for web stack

### Phase 2 — Project Management (2 weeks)
- Projects list page
- Project dashboard with health metrics
- Discovery tab: FR list, RICE scores, Gate status
- Basic document viewer (markdown rendered)

### Phase 3 — Document Management (2 weeks)
- PRD viewer with version selector
- Epic list with AC display
- CR workflow view
- Stakeholder profiles + feedback log

### Phase 4 — Polish (1 week)
- Mobile responsive optimization
- SEO metadata + sitemap
- i18n (EN/VI)
- Performance optimization
- Dark mode

---

## Docker Compose (web stack)

```yaml
services:
  web-backend:
    build: ./web/backend
    ports: ["8000:8000"]
    volumes:
      - ../:/workspace:rw  # same workspace as bot
    environment:
      - WORKSPACE_PATH=/workspace

  web-frontend:
    build: ./web/frontend
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://web-backend:8000

  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./web/nginx.conf:/etc/nginx/nginx.conf
```
