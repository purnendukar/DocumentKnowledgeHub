from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.endpoints import auth, documents
from .core.config import settings
from .db.session import get_db, Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Document Knowledge Hub API",
    description="RESTful API for Document Knowledge Hub",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    auth.router,
    prefix=settings.API_V1_STR,
    tags=["authentication"]
)

app.include_router(
    documents.router,
    prefix=f"{settings.API_V1_STR}",
    tags=["documents"]
)

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Document Knowledge Hub API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
