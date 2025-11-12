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
- **ASGI Server**: Uvicorn
- **Data Validation**: Pydantic v2
- **Migrations**: Alembic
- **Containerization**: Docker & Docker Compose
- **Architecture**: Clean architecture following SOLID principles

## Quick Start with Docker

### Prerequisites

- Docker and Docker Compose installed



### Setup Steps

1. **Clone or download the repository**

2. **Create `.env` file** (copy from `env.example`):
   ```bash
   cp env.example .env  # Linux/macOS
   copy env.example .env  # Windows
   ```

3. **Start services**:
   ```bash
   docker-compose up -d
   ```
   Migrations run automatically on startup.

4. **Access the API**:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Stop Services

```bash
docker-compose down
```

### View Logs

```bash
docker-compose logs -f api
```

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
├── docker-compose.yml  # Docker Compose configuration
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

### Review Approvals Table

Stores approval status for reviews:

- `id`: Primary key
- `review_id`: Unique review identifier (indexed)
- `listing_id`: Listing identifier (indexed, optional)
- `is_approved`: Approval status (boolean)
- `approved_at`: Timestamp when approved
- `created_at`: Record creation timestamp
- `updated_at`: Record update timestamp

## Database Migrations

### Create Migration

```bash
docker-compose exec api alembic revision --autogenerate -m "Description"
```

### Apply Migrations

```bash
docker-compose exec api alembic upgrade head
```

### Rollback Migration

```bash
docker-compose exec api alembic downgrade -1
```

## Configuration

Configuration is managed through `.env` file:

```env
# Hostaway API
HOSTAWAY_ACCOUNT_ID=61148
HOSTAWAY_API_KEY=your_api_key

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=flexreview
POSTGRES_PASSWORD=flexreview123
POSTGRES_DB=flexreview_db

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

## Local Development (Without Docker)

### Prerequisites

- Python 3.10+
- PostgreSQL 15+
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

3. **Create PostgreSQL database**:
   ```bash
   createdb flexreview_db
   ```

4. **Configure `.env`** file with database credentials

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

1. Start services: `docker-compose up -d`
2. Visit http://localhost:8000/docs
3. Test endpoints:
   - GET `/api/reviews/hostaway` - Get all reviews
   - PATCH `/api/reviews/approve` - Approve a review
   - GET `/api/reviews/approved` - Get approved reviews

### Example cURL

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

1. Check PostgreSQL is running: `docker-compose ps`
2. Verify database credentials in `.env`
3. Check logs: `docker-compose logs db`

### Migration Issues

1. Reset database: `docker-compose down -v`
2. Recreate: `docker-compose up -d`
3. Run migrations: `docker-compose exec api alembic upgrade head`

