"""
Product Management Skill Jev - FastAPI Backend
Serves the web UI and provides REST + SSE API.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers import chat, projects, settings, documents, attachments, audit


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Product Management Skill Jev web API starting...")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Product Management Skill Jev API",
    description="Web API for Product Management Skill Jev, a product management co-pilot",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router,        prefix="/api/chat",        tags=["Chat"])
app.include_router(projects.router,    prefix="/api/projects",    tags=["Projects"])
app.include_router(settings.router,    prefix="/api/settings",    tags=["Settings"])
app.include_router(documents.router,   prefix="/api/documents",   tags=["Documents"])
app.include_router(attachments.router, prefix="/api/attachments", tags=["Attachments"])
app.include_router(audit.router,       prefix="/api/audit",       tags=["Audit"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": str(exc)})
