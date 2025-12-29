# Academic Paper Analysis Tool

A full-stack web application for analyzing and visualizing academic paper citation networks using force-directed graphs. Built with FastAPI (backend), Next.js (frontend), and NetworkX for graph analysis.

---

## Features

- **Paper Search**: Query academic papers from the OpenAlex API
- **Citation Network Analysis**: Build and analyze citation relationships using NetworkX
- **Force-Directed Visualization**: Interactive graph visualization with react-force-graph-2d
- **Community Detection**: Identify research clusters using the Louvain algorithm
- **Graph Metrics**: Calculate centrality measures and clustering coefficients
- **Production-Ready**: Fully containerized with Docker, structured logging, and health checks

---

## Quick Start with Docker

Get the application running in 3 steps:

```bash
# 1. Clone repository
git clone <repository-url>
cd signal-paper-analysis

# 2. Copy environment template
cp .env.example .env

# 3. Start all services
docker-compose up -d
```

Access the application:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)

For detailed deployment instructions, see [Docker Deployment Guide](docs/deployment/docker-deployment.md).

---

## Architecture

### System Overview

```
User → Frontend (Next.js) → Backend (FastAPI) → OpenAlex API
                                    ↓
                            NetworkX Graph Analysis
```

### Technology Stack

#### Backend
- **Framework**: FastAPI 0.115+ (async/await, type hints)
- **Python**: 3.10+
- **Graph Analysis**: NetworkX 3.4+
- **HTTP Client**: httpx (async OpenAlex API calls)
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Code Quality**: black, isort, mypy

#### Frontend
- **Framework**: Next.js 14+ (App Router)
- **React**: 18+
- **Visualization**: react-force-graph-2d
- **TypeScript**: 5.0+
- **Styling**: CSS Modules (Dieter Rams design principles)
- **Testing**: Jest, React Testing Library

#### DevOps
- **Containerization**: Docker, Docker Compose
- **Orchestration**: Multi-stage builds, health checks
- **Logging**: Structured JSON logging (production)
- **CI/CD**: GitHub Actions (planned)

---

## Development

### Local Development (Without Docker)

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=app --cov-report=term-missing

# Code formatting
black app/ tests/
isort app/ tests/

# Type checking
mypy app/
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Run tests
npm test

# Run tests in watch mode
npm test -- --watch

# Build for production
npm run build

# Lint
npm run lint
```

### Docker Development (With Hot-Reload)

```bash
# Copy development environment
cp .env.development .env

# Start with development override (enables hot-reload)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Code changes in backend/app/ and frontend/src/ will auto-reload
```

---

## Testing

### Backend Testing

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_citation_network.py -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

**Test Coverage**: > 80% (unit + integration tests)

### Frontend Testing

```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage

# Run specific test file
npm test -- SearchBar.test.tsx
```

**Test Coverage**: > 80% (component + integration tests)

---

## API Documentation

### Available Endpoints

#### Health Check
```http
GET /api/health
```

**Response**:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

#### Search Papers
```http
GET /api/search?query=machine+learning&limit=50
```

**Parameters**:
- `query` (required): Search query string (1-200 characters)
- `limit` (optional): Number of papers to return (1-100, default: 50)

**Response**:
```json
{
  "nodes": [
    {
      "id": "W2123456789",
      "title": "Attention Is All You Need",
      "cited_by_count": 15000,
      "publication_year": 2017,
      "community": 0
    }
  ],
  "links": [
    {
      "source": "W2123456789",
      "target": "W2887654321"
    }
  ],
  "metadata": {
    "total_nodes": 50,
    "total_links": 120,
    "communities": 5,
    "avg_clustering": 0.35
  }
}
```

**Interactive Documentation**: http://localhost:8000/docs (Swagger UI)

---

## Docker Commands Reference

### Production Deployment

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# View service status
docker-compose ps

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Development Mode

```bash
# Start with hot-reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# View backend logs only
docker-compose logs -f backend

# View frontend logs only
docker-compose logs -f frontend

# Restart specific service
docker-compose restart backend
```

### Maintenance

```bash
# Remove all stopped containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Remove containers, volumes, and images
docker-compose down -v --rmi all

# View resource usage
docker stats

# Inspect container
docker-compose exec backend bash
docker-compose exec frontend sh
```

---

## Environment Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Logging
LOG_LEVEL=info                    # Options: debug, info, warning, error

# Backend
BACKEND_PORT=8000
OPENALEX_USER_AGENT=AcademicPaperAnalysis/1.0 (mailto:your@email.com)

# Frontend
FRONTEND_PORT=3000
NEXT_PUBLIC_API_URL=http://backend:8000

# Node Environment
NODE_ENV=production               # Options: development, staging, production
```

**Important**: Replace `your@email.com` with your actual email to access OpenAlex's polite pool (higher rate limits).

### Environment Presets

| File | Use Case | LOG_LEVEL | NODE_ENV |
|------|----------|-----------|----------|
| `.env.development` | Local development | debug | development |
| `.env.staging` | Pre-production testing | info | staging |
| `.env.production` | Production deployment | warning | production |

---

## Project Structure

```
signal-paper-analysis/
├── backend/                      # FastAPI backend
│   ├── app/
│   │   ├── api/                 # API routes
│   │   │   └── routes.py        # /api/health, /api/search
│   │   ├── services/            # Business logic
│   │   │   ├── openalex_client.py     # OpenAlex API client
│   │   │   └── citation_network.py    # NetworkX graph builder
│   │   ├── models/              # Pydantic schemas
│   │   │   └── schemas.py       # GraphResponse, HealthResponse
│   │   ├── utils/               # Utilities
│   │   │   ├── errors.py        # Custom exceptions
│   │   │   └── logger.py        # Structured logging
│   │   └── main.py              # FastAPI app entry point
│   ├── tests/                   # pytest tests
│   ├── Dockerfile               # Multi-stage backend image
│   └── requirements.txt         # Python dependencies
│
├── frontend/                     # Next.js frontend
│   ├── src/
│   │   ├── app/                 # Next.js App Router
│   │   ├── components/          # React components
│   │   │   ├── SearchBar.tsx    # Search input
│   │   │   ├── ForceGraph.tsx   # D3 force-directed graph
│   │   │   └── Metadata.tsx     # Graph statistics
│   │   └── styles/              # CSS Modules
│   ├── __tests__/               # Jest tests
│   ├── Dockerfile               # Multi-stage frontend image
│   └── package.json             # npm dependencies
│
├── docs/
│   ├── deployment/
│   │   └── docker-deployment.md # Detailed deployment guide
│   └── diagrams/                # Architecture diagrams (Mermaid)
│
├── .env.example                 # Environment template
├── .env.development             # Development preset
├── .env.staging                 # Staging preset
├── .env.production              # Production preset
├── docker-compose.yml           # Production orchestration
├── docker-compose.dev.yml       # Development override
└── README.md                    # This file
```

---

## Troubleshooting

### Backend Issues

#### Health Check Fails

```bash
# Check backend logs
docker-compose logs backend

# Verify backend is responding
curl http://localhost:8000/api/health

# Restart backend
docker-compose restart backend
```

#### OpenAlex API Errors

**Error**: "Request timeout after 30s"

**Solution**: Check internet connection, verify OpenAlex API status at https://openalex.org/

**Error**: "Rate limit exceeded"

**Solution**: Add your email to `OPENALEX_USER_AGENT` in `.env`:
```bash
OPENALEX_USER_AGENT=AcademicPaperAnalysis/1.0 (mailto:your@email.com)
```

### Frontend Issues

#### Cannot Connect to Backend

**Error**: "Failed to fetch" or "Network error"

**Solution**:

```bash
# Verify backend is healthy
docker-compose ps

# Check frontend environment
docker-compose exec frontend env | grep NEXT_PUBLIC_API_URL

# Should show: NEXT_PUBLIC_API_URL=http://backend:8000

# Restart frontend
docker-compose restart frontend
```

### Docker Issues

#### Port Already in Use

**Error**: `bind: address already in use`

**Solution**:

```bash
# Change ports in .env
BACKEND_PORT=8001
FRONTEND_PORT=3001

# Or kill conflicting process (find PID first)
# macOS/Linux: lsof -i :8000
# Windows: netstat -ano | findstr :8000
```

For more troubleshooting, see [Docker Deployment Guide](docs/deployment/docker-deployment.md#troubleshooting).

---

## Contributing

### Development Workflow

1. **Create feature branch**: `git checkout -b feature/your-feature`
2. **Write tests first** (TDD): Red → Green → Refactor
3. **Implement feature** with transparent error handling
4. **Run tests**: Ensure > 80% coverage
5. **Format code**: `black`, `isort` (backend), `npm run lint` (frontend)
6. **Type check**: `mypy app/` (backend)
7. **Commit**: Follow conventional commits (feat:, fix:, docs:)
8. **Push and create PR**

### Code Quality Standards

- **Test Coverage**: > 80% (measured by pytest-cov)
- **Type Annotations**: All functions must have type hints
- **Error Handling**: Never hide errors, always provide context
- **Documentation**: API endpoints, complex algorithms
- **Design Principles**: Follow Dieter Rams' 10 principles (frontend)

---

## License

MIT License - See LICENSE file for details

---

## Contact & Support

- **Documentation**: See `docs/` directory
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Issues**: Report bugs via GitHub Issues
- **OpenAlex API**: https://docs.openalex.org/

---

**Last Updated**: 2025-12-28
**Version**: 1.0.0
**Status**: Production Ready
