# Flex Living Reviews Backend API

Backend API for the Flex Living Reviews Dashboard, built with FastAPI, PostgreSQL, and Docker.

## Overview

This API provides normalized review data from various sources (currently Hostaway) for the Flex Living Reviews Dashboard. The system includes:
- Review normalization and data management
- **Review approval system** - Managers can approve/reject reviews for public display
- PostgreSQL database for persistence
- Docker containerization for easy deployment
- Rate limiting and comprehensive logging

## Tech Stack

- **Python**: 3.10+
- **Framework**: FastAPI
- **Database**: PostgreSQL 16 (async with SQLAlchemy)
  - Development: Included in `docker-compose.dev.yml`
  - Production: External database (configured via `.env`)
- **ASGI Server**: Uvicorn
- **Data Validation**: Pydantic v2
- **Migrations**: Alembic
- **Containerization**: Docker & Docker Compose
- **Architecture**: Clean architecture following SOLID principles

## Quick Start with Docker

### Prerequisites

- Docker and Docker Compose installed

### Development Setup (with Local Database)

For local development with a PostgreSQL database container:

1. **Clone or download the repository**

2. **Create `.env` file** (copy from `env.example`):
   ```bash
   cp env.example .env  # Linux/macOS
   copy env.example .env  # Windows
   ```

3. **Start services** (includes PostgreSQL database):
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```
   Migrations run automatically on startup.

4. **Access the API**:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

5. **Stop services**:
   ```bash
   docker-compose -f docker-compose.dev.yml down
   ```

6. **View logs**:
   ```bash
   docker-compose -f docker-compose.dev.yml logs -f api
   ```

### Production Setup (External Database)

For production deployment with an existing PostgreSQL database:

1. **Create `.env` file** with production database credentials:
   ```bash
   cp env.example .env
   ```
   
   Update the following variables in `.env`:
   ```env
   DATABASE_URL=postgresql+psycopg://user:password@your-db-host:5432/your-db-name
   POSTGRES_HOST=your-db-host
   POSTGRES_PORT=5432
   POSTGRES_USER=your-db-user
   POSTGRES_PASSWORD=your-db-password
   POSTGRES_DB=your-db-name
   API_PORT=8005
   ```

2. **Start API service** (database runs separately):
   ```bash
   docker-compose up -d
   ```
   Migrations run automatically on startup.

3. **Access the API**:
   - API: http://localhost:8005
   - API Docs: http://localhost:8005/docs
   - Health Check: http://localhost:8005/health

4. **Stop service**:
   ```bash
   docker-compose down
   ```

### Docker Compose Files

- **`docker-compose.dev.yml`**: Development setup with PostgreSQL container
  - Includes database service
  - Hot reload enabled
  - Port 8000
  - Auto-creates database volume

- **`docker-compose.yml`**: Production setup (API only)
  - No database container (uses external DB)
  - Port 8005
  - Optimized for production

## Project Structure

```
flex-review-backend/
├── app/
│   ├── core/           # Core configuration and utilities
│   │   ├── config.py   # Application settings
│   │   └── logging_config.py # Logging setup
│   ├── database/       # Database configuration
│   │   ├── base.py     # Database connection
│   │   └── models.py   # SQLAlchemy models
│   ├── middleware/     # Middleware components
│   │   ├── request_logging.py
│   │   └── rate_limiting.py
│   ├── routes/         # API route handlers
│   │   └── reviews.py  # Review endpoints
│   ├── services/       # Business logic layer
│   │   ├── hostaway.py # Hostaway data service
│   │   ├── normalizer.py # Review normalization
│   │   └── review_approval.py # Approval service
│   ├── models.py       # Pydantic data models
│   └── main.py         # FastAPI application entry point
├── alembic/            # Database migrations
├── data/               # Mock data files
├── docker-compose.yml  # Production Docker Compose (API only, external DB)
├── docker-compose.dev.yml  # Development Docker Compose (API + PostgreSQL)
├── Dockerfile          # Docker image definition
└── requirements.txt    # Python dependencies
```

## API Endpoints

### Review Management

#### Get All Reviews
```
GET /api/reviews/hostaway
```
Returns all Hostaway reviews with approval status from database.

**Response**: Array of normalized review objects with `isApproved` field

#### Toggle Review Approval
```
PATCH /api/reviews/approve
```
Approve or reject a single review for public display.

**Request Body**:
```json
{
  "review_id": 7453,
  "is_approved": true
}
```

**Response**:
```json
{
  "success": true,
  "review_id": 7453,
  "is_approved": true,
  "message": "Review 7453 approved"
}
```

#### Bulk Toggle Review Approvals
```
PATCH /api/reviews/approve/bulk
```
Approve or reject multiple reviews at once.

**Request Body**:
```json
{
  "review_ids": [7453, 7454, 7455],
  "is_approved": true
}
```

**Response**:
```json
{
  "success": true,
  "updated_count": 3,
  "is_approved": true,
  "message": "3 reviews approved"
}
```

#### Get Approved Reviews
```
GET /api/reviews/approved?listing_id=FLX-307
```
Get list of approved review IDs (for public display page).

**Query Parameters**:
- `listing_id` (optional): Filter by listing ID

**Response**:
```json
{
  "approved_review_ids": [7453, 7454],
  "count": 2
}
```

### Health Check

```
GET /health
```

Returns API health status.

## Database Schema

### Reviews Table

Stores all review data in the database:

- `id`: Primary key (review ID)
- `listing_id`: Listing identifier (indexed, optional)
- `listing_name`: Name of the listing (indexed)
- `listing_location`: Location of the listing
- `channel`: Review source channel (airbnb, booking, direct, vrbo, hostaway) (indexed)
- `type`: Review type (host-to-guest, guest-to-host) (indexed)
- `status`: Review status (published, draft, etc.) (indexed)
- `rating`: Overall rating (0-10, nullable)
- `overall_rating`: Alias for rating (nullable)
- `category_ratings`: JSON object with category ratings (e.g., {"cleanliness": 10})
- `public_review`: Public review text
- `private_note`: Private/internal notes
- `guest_name`: Guest name (nullable)
- `submitted_at`: Review submission timestamp (indexed)
- `stay_date`: Date of stay (YYYY-MM-DD format)
- `stay_length`: Length of stay in days
- `is_approved`: Approval status for public display (indexed)
- `approved_at`: Timestamp when approved
- `created_at`: Record creation timestamp
- `updated_at`: Record update timestamp

**Indexes:**
- `idx_review_listing_approved`: Composite index on `listing_id` and `is_approved`
- `idx_review_channel_status`: Composite index on `channel` and `status`
- `idx_review_submitted_at`: Index on `submitted_at`
- `idx_review_approved`: Index on `is_approved`

## Database Migrations

### Create Migration

**Development:**
```bash
docker-compose -f docker-compose.dev.yml exec api alembic revision --autogenerate -m "Description"
```

**Production:**
```bash
docker-compose exec api alembic revision --autogenerate -m "Description"
```

### Apply Migrations

**Development:**
```bash
docker-compose -f docker-compose.dev.yml exec api alembic upgrade head
```

**Production:**
```bash
docker-compose exec api alembic upgrade head
```

**Note**: Migrations run automatically on container startup in both setups.

### Rollback Migration

**Development:**
```bash
docker-compose -f docker-compose.dev.yml exec api alembic downgrade -1
```

**Production:**
```bash
docker-compose exec api alembic downgrade -1
```

## Configuration

Configuration is managed through `.env` file. All variables are loaded automatically via `env_file` in Docker Compose.

### Required Environment Variables

```env
# Hostaway API Configuration
HOSTAWAY_ACCOUNT_ID=61148
HOSTAWAY_API_KEY=your_api_key

# Application Port
API_PORT=8000  # Development (docker-compose.dev.yml)
# API_PORT=8005  # Production (docker-compose.yml)

# Database Configuration
# For development: docker-compose.dev.yml automatically sets POSTGRES_HOST=db
# For production: Set to your external database host
DATABASE_URL=postgresql+psycopg://flexreview:flexreview123@localhost:5432/flexreview_db
POSTGRES_HOST=localhost  # Use 'db' for Docker network (dev), your-host for production
POSTGRES_PORT=5432
POSTGRES_USER=flexreview
POSTGRES_PASSWORD=flexreview123
POSTGRES_DB=flexreview_db
DATABASE_ECHO=false

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Logging Configuration
LOG_LEVEL=INFO
# LOG_FILE=logs/app.log

# Rate Limiting Configuration
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

### Production Database Configuration

For production with external database, update these variables in `.env`:

```env
DATABASE_URL=postgresql+psycopg://production_user:production_password@your-db-host:5432/production_db
POSTGRES_HOST=your-db-host
POSTGRES_USER=production_user
POSTGRES_PASSWORD=production_password
POSTGRES_DB=production_db
API_PORT=8005
```

**Note**: 
- Development (`docker-compose.dev.yml`) automatically overrides `POSTGRES_HOST=db` and rebuilds `DATABASE_URL` for Docker networking
- Production (`docker-compose.yml`) uses the values directly from `.env` file

## Local Development (Without Docker)

### Prerequisites

- Python 3.10+
- PostgreSQL 16+ (or use Docker for database only)
- pip

### Setup

1. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up database** (choose one):
   
   **Option A: Use Docker for database only**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d db
   ```
   
   **Option B: Use local PostgreSQL**
   ```bash
   createdb flexreview_db
   ```

4. **Configure `.env`** file with database credentials:
   ```env
   DATABASE_URL=postgresql+psycopg://flexreview:flexreview123@localhost:5432/flexreview_db
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_USER=flexreview
   POSTGRES_PASSWORD=flexreview123
   POSTGRES_DB=flexreview_db
   ```

5. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Start server**:
   ```bash
   uvicorn app.main:app --reload
   ```

## Features

###  Task Requirements 

1. **Hostaway Integration** 
   - Mocked review data
   - Normalization by listing, type, channel, and date
   - `/api/reviews/hostaway` endpoint implemented

2. **Manager Dashboard Support** 
   - Filter/sort by rating, category, channel, time
   - **Review approval system** - Select which reviews display publicly
   - Approval status persisted in PostgreSQL

3. **Review Display Page Support** 
   - `/api/reviews/approved` endpoint for public display
   - Only approved reviews returned
   - Filterable by listing ID

4. **Google Reviews (Exploration)** 
   - Architecture supports future integration
   - See README for findings

### Additional Features

- **Docker & Docker Compose** - Easy deployment
- **PostgreSQL Integration** - Persistent approval storage
- **Rate Limiting** - API protection
- **Comprehensive Logging** - Request tracking
- **Database Migrations** - Version-controlled schema
- **Bulk Operations** - Efficient approval management

## API Documentation

Interactive API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

### Manual Testing

**Development:**
```bash
docker-compose -f docker-compose.dev.yml up -d
# API available at http://localhost:8000
```

**Production:**
```bash
docker-compose up -d
# API available at http://localhost:8005
```

Visit the API docs:
- Development: http://localhost:8000/docs
- Production: http://localhost:8005/docs

Test endpoints:
- GET `/api/reviews/hostaway` - Get all reviews
- PATCH `/api/reviews/approve` - Approve a review
- GET `/api/reviews/approved` - Get approved reviews

### Example cURL

**Development (port 8000):**
```bash
# Get all reviews
curl http://localhost:8000/api/reviews/hostaway

# Approve a review
curl -X PATCH http://localhost:8000/api/reviews/approve \
  -H "Content-Type: application/json" \
  -d '{"review_id": 7453, "is_approved": true}'

# Get approved reviews
curl http://localhost:8000/api/reviews/approved
```

**Production (port 8005):**
```bash
# Replace 8000 with 8005 in all URLs
curl http://localhost:8005/api/reviews/hostaway
```

## Rate Limiting

- Default: 60 requests/minute, 1000 requests/hour per IP
- Configurable via environment variables
- Health check and docs exempt from rate limiting
- Rate limit headers included in responses

## Logging

- Request logging with IP tracking
- Unique request IDs for tracing
- Configurable log levels
- Optional file logging

## Design Principles

- **SOLID**: Single Responsibility, Open/Closed, Dependency Inversion
- **DRY**: Reusable services and middleware
- **Clean Architecture**: Separation of concerns
- **Type Safety**: Pydantic models throughout

## Troubleshooting

### Database Connection Issues

**Development (docker-compose.dev.yml):**
1. Check PostgreSQL is running: `docker-compose -f docker-compose.dev.yml ps`
2. Verify database credentials in `.env`
3. Check logs: `docker-compose -f docker-compose.dev.yml logs db`
4. Ensure `POSTGRES_HOST=db` is set (automatically overridden in docker-compose.dev.yml)

**Production (docker-compose.yml):**
1. Verify external database is accessible from the container
2. Check database credentials in `.env` match your production database
3. Test connection: `docker-compose exec api python -c "from app.database.base import engine; import asyncio; asyncio.run(engine.connect())"`
4. Ensure `POSTGRES_HOST` points to your production database host (not 'db' or 'localhost')

### Migration Issues

**Development:**
```bash
# Reset database (⚠️ deletes data)
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
# Migrations run automatically
```

**Production:**
```bash
# Run migrations manually
docker-compose exec api alembic upgrade head
```

### Port Conflicts

- Development uses port **8000** (`docker-compose.dev.yml`)
- Production uses port **8005** (`docker-compose.yml`)
- Change `API_PORT` in `.env` if needed

### Environment Variables Not Loading

- Ensure `.env` file exists in project root
- Check `env_file: .env` is present in docker-compose.yml
- Verify no syntax errors in `.env` file (no spaces around `=`)
- Restart containers after changing `.env`: `docker-compose restart api`

