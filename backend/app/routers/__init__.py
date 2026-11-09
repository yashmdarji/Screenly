from backend.app.routers.session_routes import router as session_router
from backend.app.routers.interview_routes import router as interview_router
from backend.app.routers.resume_routes import router as resume_router
from backend.app.routers.knowledge_routes import router as knowledge_router

__all__ = [
    "session_router",
    "interview_router",
    "resume_router",
    "knowledge_router",
]
