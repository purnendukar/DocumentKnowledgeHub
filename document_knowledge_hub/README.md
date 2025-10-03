# Document Knowledge Hub

A secure, scalable document management and knowledge extraction system built with FastAPI and modern Python.

## 📋 Features

- **User Authentication** - JWT-based authentication system
- **Document Management** - Upload, view, update, and delete documents
- **Text Extraction** - Extract text from PDF and DOCX files
- **Search** - Full-text search across all documents
- **RESTful API** - Clean, well-documented API endpoints
- **Docker Support** - Easy containerization and deployment
- **Rate Limiting** - Protect your API from abuse
- **SQLAlchemy ORM** - Database abstraction layer

## 🚀 Tech Stack

- **Backend**: FastAPI (Python 3.12+)
- **Database**: SQLite (development), PostgreSQL (production-ready)
- **Authentication**: JWT (JSON Web Tokens)
- **Containerization**: Docker + Docker Compose
- **Package Management**: Poetry
- **Testing**: Pytest
- **Documentation**: OpenAPI (Swagger UI)

## 🛠️ Prerequisites

- Python 3.12+
- Docker & Docker Compose (for containerized deployment)
- Poetry (for dependency management)

## 🏗️ Project Structure

```
.
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py       # Authentication endpoints
│   │       │   └── documents.py  # Document management endpoints
│   │       └── __init__.py
│   ├── core/
│   │   ├── config.py    # Application configuration
│   │   └── security.py  # Authentication and security utilities
│   ├── db/
│   │   ├── base.py      # SQLAlchemy base models
│   │   ├── session.py   # Database session management
│   │   └── models/      # Database models
│   ├── schemas/         # Pydantic models for request/response
│   └── utils/           # Utility functions
├── migrations/          # Database migrations (Alembic)
├── tests/               # Test files
├── .env.example         # Example environment variables
├── docker-compose.yml   # Docker Compose configuration
├── Dockerfile           # Docker configuration
└── pyproject.toml       # Project dependencies and metadata
```

## 🚀 Getting Started

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/purnendukar/DocumentKnowledgeHub.git
   cd DocumentKnowledgeHub/document_knowledge_hub
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**
   ```bash
   poetry install
   ```

4. **Start the development server**
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Setup

1. **Build and start the containers**
   ```bash
   docker-compose up --build
   ```

2. **Access the application**
   - API Docs (Swagger UI): http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 🔒 Authentication

The API uses JWT for authentication. To authenticate your requests:

1. Get an access token:
   ```bash
   curl -X 'POST' \
     'http://localhost:8000/api/v1/auth/login' \
     -H 'accept: application/json' \
     -H 'Content-Type: application/x-www-form-urlencoded' \
     -d 'username=testuser&password=testpass'
   ```

2. Use the token in subsequent requests:
   ```
   Authorization: Bearer <your_token_here>
   ```

## 📚 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Get access token
- `POST /api/v1/auth/register` - Register new user

### Documents
- `GET /api/v1/documents` - List all documents
- `GET /api/v1/documents/{id}` - Get document by ID
- `POST /api/v1/documents` - Upload new document
- `PUT /api/v1/documents/{id}` - Update document
- `DELETE /api/v1/documents/{id}` - Delete document
- `GET /api/v1/documents/search` - Search documents

## 🧪 Running Tests

```bash
pytest tests/
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the amazing web framework
- SQLAlchemy for the ORM
- All the open-source libraries used in this project
