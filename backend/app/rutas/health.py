"""
Health check endpoints for container orchestration and monitoring.
"""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
import time

from ..datos.db import get_db
from ..config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Liveness probe - is the application running?

    Used by Docker, Kubernetes, load balancers to determine if the container is alive.
    Returns 200 if the app process is running.
    """
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness probe - can the application serve traffic?

    Used by Kubernetes to determine if the pod should receive traffic.
    Checks:
    - Database connectivity
    - Database response time

    Returns:
    - 200 if ready to serve traffic
    - 503 if not ready (slow DB, DB down, etc.)
    """
    try:
        start = time.time()
        # Simple query to verify DB connection
        db.execute(text("SELECT 1"))
        db_latency = time.time() - start

        # If DB is too slow, mark as not ready
        if db_latency > 1.0:
            return Response(
                content='{"status":"degraded","database":"slow","db_latency_ms":' + str(round(db_latency * 1000, 2)) + '}',
                status_code=503,
                media_type="application/json"
            )

        return {
            "status": "ready",
            "database": "healthy",
            "db_latency_ms": round(db_latency * 1000, 2)
        }

    except Exception as e:
        return Response(
            content=f'{{"status":"not_ready","error":"{str(e)}"}}',
            status_code=503,
            media_type="application/json"
        )


@router.get("/health/startup")
async def startup_check(db: Session = Depends(get_db)):
    """
    Startup probe - has the application finished initialization?

    Used by Kubernetes to wait for slow-starting containers.
    Similar to readiness but with more lenient timeout expectations.
    """
    try:
        # Verify database connection
        db.execute(text("SELECT 1"))

        # Check if critical tables exist (verify migrations ran)
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'usuarios'
            )
        """))
        tables_exist = result.scalar()

        if not tables_exist:
            return Response(
                content='{"status":"not_started","error":"Database migrations not completed"}',
                status_code=503,
                media_type="application/json"
            )

        return {
            "status": "started",
            "database": "connected",
            "migrations": "completed"
        }

    except Exception as e:
        return Response(
            content=f'{{"status":"not_started","error":"{str(e)}"}}',
            status_code=503,
            media_type="application/json"
        )
