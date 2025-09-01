from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import socketio
import uvicorn
import sys
import os
from pathlib import Path

# Add parent directory to path to import ADK agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from api import auth, chat, lists_firestore as lists, agent, maps, sessions, query, videos, visualize, documents
from api import settings as settings_api
from core.websocket import sio, sio_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    yield
    # Shutdown
    print("Shutting down...")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(lists.router, prefix="/api/lists", tags=["Lists"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
app.include_router(maps.router, prefix="/api/maps", tags=["Maps"])
app.include_router(query.router, prefix="/api", tags=["Query"])
app.include_router(videos.router, prefix="/api/videos", tags=["Videos"])
app.include_router(visualize.router, prefix="/api", tags=["Visualize"])
app.include_router(settings_api.router, prefix="/api", tags=["Settings"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])

# Mount Socket.IO app
app.mount("/socket.io", sio_app)

# Serve static files in production
if not settings.DEBUG:
    # Get the frontend build directory
    frontend_build_dir = Path(__file__).parent.parent / "frontend" / "build"
    
    if frontend_build_dir.exists():
        # Mount static files
        app.mount("/static", StaticFiles(directory=str(frontend_build_dir / "static")), name="static")
        
        # Serve public files (like logo) at root
        @app.get("/greywolf_logo.png")
        async def serve_logo():
            logo_path = frontend_build_dir / "greywolf_logo.png"
            if logo_path.exists():
                return FileResponse(str(logo_path))
            return {"error": "Logo not found"}, 404
        
        # Serve index.html for all non-API routes (React routing)
        @app.get("/{full_path:path}")
        async def serve_react_app(full_path: str):
            from fastapi import HTTPException
            # Don't serve React app for API routes
            if full_path.startswith("api/") or full_path.startswith("socket.io/"):
                raise HTTPException(status_code=404, detail="Not found")
            
            # Check if it's a file in the build directory
            if "." in full_path:
                file_path = frontend_build_dir / full_path
                if file_path.exists():
                    return FileResponse(str(file_path))
            
            index_path = frontend_build_dir / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))
            return {"error": "Frontend not built"}, 404

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
        # Increase limits for video uploads
        limit_max_requests=100000,
        h11_max_incomplete_event_size=1024 * 1024 * 1024  # 1GB
    )