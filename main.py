import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from config.logging_config import logger
from config.settings import settings

# Routers
from app.api.primary_agent_handler import primary_agent_handler_router

# ─────────────────────────────────────────────────────────────────────────────

try:
    load_dotenv()
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error loading environment variables: {e}")

# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")
    yield
    logger.info("Application shutdown")

app = FastAPI(
    title=settings.APP_NAME,
    description="AI microservice for education + agent functionality.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
    contact={
        "name": "Support",
        "url": "https://example.com/support",
        "email": "support@example.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# ─────────────────────────────────────────────────────────────────────────────

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────

# Register routers
app.include_router(primary_agent_handler_router, prefix="", tags=["Primary Agent Handler"])

# ─────────────────────────────────────────────────────────────────────────────

@app.get("/ping", tags=["Health"])
def ping():
    logger.info("Ping endpoint accessed")
    return {"message": "pong"}

@app.get("/", tags=["Root"])
async def root():
    return {"message": f"{settings.APP_NAME} is running."}

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Status code: {response.status_code}")
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
