from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.extension import Limiter as SlowLimiter
from slowapi.util import get_remote_address

from .database import init_db
from .routes import auth_routes, docs_routes

import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Document Knowledge Hub", version="1.0")

# Initialize DB (create tables)
init_db()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach routers
app.include_router(auth_routes.router)
app.include_router(docs_routes.router)

# slowapi setup (global)
limiter = SlowLimiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware to optionally set request.state.user_key for per-user limiter in docs_routes
@app.middleware("http")
async def attach_user_key(request: Request, call_next):
    # leave token in state for per-user key in docs_routes limiter (already handled there)
    return await call_next(request)
