import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.config import settings
from backend.app.database import init_db
from backend.app.routers import (
    session_router,
    interview_router,
    resume_router,
    knowledge_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database schema and ensures vector store readiness on startup."""
    init_db()
    print("[Startup] SQLite database initialized successfully.")
    yield
    print("[Shutdown] Screenly server stopped.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Role-adaptive candidate technical screening system powered by textbook-grounded RAG",
    lifespan=lifespan
)

# Enable CORS for local frontend development (Vite, Next.js, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(session_router)
app.include_router(interview_router)
app.include_router(resume_router)
app.include_router(knowledge_router)


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER
    }


# Static frontend mounting for single-command run
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        # Don't intercept API routes
        if full_path.startswith("api"):
            return None
        file_target = STATIC_DIR / full_path
        if file_target.exists() and file_target.is_file():
            return FileResponse(file_target)
        return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
