from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.users.router import router as users_router
from app.auth.router import router as auth_router
from app.products.router import router as products_router
from app.logs.logger import setup_logger
import time

logger = setup_logger()

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── MIDDLEWARES ────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logger(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} "
        f"- {response.status_code} "
        f"- {process_time:.2f}s"
    )
    return response


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# ── ROUTERS ────────────────────────────────────────────────────────────────────
app.include_router(auth_router,     prefix="/api/v1")
app.include_router(users_router,    prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")
