# Docker Compose Setup

## Quick Start

### Production Mode
```bash
# Copy environment file
cp .env.example .env

# Edit .env and set your passwords and keys
nano .env

# Build and start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f
```

### Development Mode
```bash
# Copy and configure for development
cp .env.example .env

# Edit .env and uncomment development overrides:
# BUILD_TARGET=development
# VOLUME_MODE=rw
# DEBUG=true
# NODE_ENV=development

# Start services with live reload
docker-compose up
```

## Services

- **db**: PostgreSQL 15 database (port 5432)
- **backend**: Django/Python API (port 8000)
- **frontend-student**: Student portal React app (port 3000)
- **frontend-admin**: Admin portal React app (port 3001)

## URLs

- Student Portal: http://localhost:3000
- Admin Portal: http://localhost:3001
- Shared public-origin admin route: `/admin/` on the student portal host (HTTPS when served behind the production TLS proxy)
- Backend API: http://localhost:8000
- Database: localhost:5432

## Useful Commands

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (deletes database data)
docker-compose down -v

# Rebuild specific service
docker-compose build backend

# View logs for specific service
docker-compose logs -f backend

# Execute command in running container
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser

# Access database
docker-compose exec db psql -U maxhack_user -d maxhack

# Restart a service
docker-compose restart backend
```

These Docker Compose commands show logs only where the Compose project is available. This repository does not document a separate production log host, systemd unit, or remote log viewer.

## Health Checks

All services have health checks configured:
- Database: PostgreSQL ready check
- Backend: `/api/health/` endpoint (curl check)
- Frontends: `/health` endpoint (nginx check)

## Production Deployment

1. Update `.env` with production values:
   - Strong `SECRET_KEY`
   - Secure `DB_PASSWORD`
   - Proper `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`
   - Production API URL for frontends

2. Ensure `BUILD_TARGET=production` in `.env`

3. Use proper SSL/TLS termination (nginx, load balancer, or reverse proxy)

4. Consider using Docker secrets for sensitive data

5. Set up proper backup strategy for `postgres_data` volume

## Volume Mounts

- `postgres_data`: Database persistent storage
- `backend_media`: User uploaded files
- `backend_static`: Static assets (CSS, JS, images)

## Multi-stage Builds

All Dockerfiles use multi-stage builds:
- **Development stage**: Includes dev tools, hot reload
- **Builder stage**: Compiles/builds the application
- **Production stage**: Minimal runtime with only necessary files

Switch between stages using `BUILD_TARGET` environment variable.
