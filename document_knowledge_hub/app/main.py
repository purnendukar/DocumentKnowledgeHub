from fastapi import FastAPI, status, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder
from typing import Optional
import json

from .api.v1.endpoints import auth, documents
from .core.config import settings
from .db.session import get_db, Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Document Knowledge Hub API",
        version="1.0.0",
        description="""
        ## 📚 Document Knowledge Hub API
        
        A secure, scalable document management and knowledge extraction system.
        
        ### Key Features:
        - 🔐 JWT Authentication
        - 📄 Document Management (Upload, Retrieve, Search)
        - 🔍 Full-text Search
        - ⚡ FastAPI & Python 3.12+
        - 🐳 Docker Ready
        
        ### Authentication
        Most endpoints require authentication. Use the `/auth/login` endpoint to get a JWT token.
        
        ### Rate Limiting
        - 100 requests per minute per user
        
        ### Error Responses
        - `400`: Bad Request
        - `401`: Unauthorized
        - `403`: Forbidden
        - `404`: Not Found
        - `422`: Validation Error
        - `429`: Too Many Requests
        - `500`: Internal Server Error
        """,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": f"{settings.API_V1_STR}/auth/login",
                    "scopes": {}
                }
            }
        }
    }
    
    # Add global security
    openapi_schema["security"] = [{"OAuth2PasswordBearer": []}]
    
    # Add more detailed error responses
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if "responses" not in method:
                method["responses"] = {}
            
            # Add common error responses
            method["responses"].update({
                "400": {"description": "Bad Request"},
                "401": {"description": "Unauthorized"},
                "403": {"description": "Forbidden"},
                "404": {"description": "Not Found"},
                "422": {"description": "Validation Error"},
                "429": {"description": "Too Many Requests"},
                "500": {"description": "Internal Server Error"},
            })
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app = FastAPI(
    title="Document Knowledge Hub API",
    description="""
    ## 📚 Document Knowledge Hub API
    
    A secure, scalable document management and knowledge extraction system.
    
    ### Key Features:
    - 🔐 JWT Authentication
    - 📄 Document Management (Upload, Retrieve, Search)
    - 🔍 Full-text Search
    - ⚡ FastAPI & Python 3.12+
    - 🐳 Docker Ready
    
    ### Authentication
    Most endpoints require authentication. Use the `/auth/login` endpoint to get a JWT token.
    
    ### Rate Limiting
    - 100 requests per minute per user
    """,
    version="1.0.0",
    contact={
        "name": "Support",
        "email": "support@documenthub.example.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=None,  # Disable default Swagger UI
    redoc_url=None,  # Disable default ReDoc
)

# Set the custom OpenAPI schema
app.openapi = custom_openapi

# Custom Swagger UI HTML
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.0.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.0.0/swagger-ui.css",
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,
            "persistAuthorization": True,
            "displayRequestDuration": True,
            "filter": True,
            "syntaxHighlight.theme": "monokai"
        }
    )

# Custom ReDoc HTML
@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=app.title + " - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        with_google_fonts=False,
        hide_hostname=True
    )

# Redirect root to docs
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

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
