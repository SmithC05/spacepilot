from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine
from . import models
from .routes import rooms, bookings, people, events, navigation, policies

# Create all database tables on startup (no migration needed for SQLite dev)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SpacePilot API",
    description="AI-powered workspace operations assistant",
    version="0.1.0",
)

# Allow the Next.js frontend to call this API during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(rooms.router)
app.include_router(bookings.router)
app.include_router(people.router)
app.include_router(events.router)
app.include_router(navigation.router)
app.include_router(policies.router)


@app.get("/health", tags=["health"])
def health_check():
    """Simple health check — used by the frontend to verify connectivity."""
    return {"status": "ok", "service": "SpacePilot API"}
