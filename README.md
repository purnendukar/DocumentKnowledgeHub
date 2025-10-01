# Document Knowledge Hub (FastAPI)

## Overview
A Document Knowledge Hub built with FastAPI that supports upload of PDF/DOCX/TXT files, text extraction, search, JWT authentication, and rate limiting. This project uses Poetry for dependency management and packaging.

## 🚀 Features
- 📄 Upload and manage documents (PDF, DOCX, TXT)
- 🔍 Extract metadata and text content using PyPDF2 and python-docx
- 💾 Store document metadata and content in SQLite database
- 🔑 JWT-based authentication (register/login)
- 🔎 Full-text search across document content
- ⏱️ Per-user rate limiting (100 requests/min)
- 📚 Interactive API documentation with Swagger UI and ReDoc
- 🐳 Docker support for easy deployment

## 🛠️ Prerequisites
- Python 3.12 or higher
- [Poetry](https://python-poetry.org/) for dependency management
- (Optional) Docker and Docker Compose

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/purnendukar/DocumentKnowledgeHub.git
cd DocumentKnowledgeHub
```

### 2. Set up environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your configuration
# nano .env
```

### 3. Install dependencies
Using Poetry (recommended):
```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### 4. Run database migrations
```bash
alembic upgrade head
```

### 5. Start the development server
```bash
uvicorn document_knowledge_hub.app.main:app --reload
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation
- Interactive API docs (Swagger UI): `http://localhost:8000/docs`
- Alternative API docs (ReDoc): `http://localhost:8000/redoc`

## 🐳 Docker Setup
```bash
# Build and start the containers
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f
```

## 🧪 Running Tests
```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=document_knowledge_hub tests/
```

## 🛠️ Development

### Adding new dependencies
```bash
# Add a production dependency
poetry add package_name

# Add a development dependency
poetry add --group dev package_name
```

### Database Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head
```

## 📝 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
