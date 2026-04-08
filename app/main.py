from sqlalchemy import text

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import register_middleware
from app.db.session import AsyncSessionLocal
from app.queue.redis_client import get_redis_client


def create_application() -> FastAPI:
    configure_logging(settings.app_debug, settings.log_level)
    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        version="0.1.0",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json" if settings.app_env == "development" else None,
        docs_url="/docs" if settings.app_env == "development" else None,
        redoc_url="/redoc" if settings.app_env == "development" else None,
    )
    register_middleware(app)
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["health"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok", "environment": settings.app_env}

    @app.get("/health/live", tags=["health"])
    async def liveness_check() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    async def readiness_check() -> dict[str, object]:
        db_ok = False
        redis_ok = False
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            db_ok = False
        try:
            redis_client = get_redis_client()
            redis_ok = bool(await redis_client.ping())
        except Exception:
            redis_ok = False
        status_value = "ok" if db_ok and redis_ok else "degraded"
        payload = {
            "status": status_value,
            "checks": {
                "database": db_ok,
                "redis": redis_ok,
            },
        }
        if status_value != "ok":
            return JSONResponse(status_code=503, content=payload)
        return payload

    return app


app = create_application()
