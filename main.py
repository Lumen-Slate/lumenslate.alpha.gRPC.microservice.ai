from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from config.logging_config import logger
from config.settings import settings

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

# This application now only supports gRPC.
# All REST API endpoints and FastAPI setup have been removed.
# Use grpc_server.py as the main entry point for the gRPC server.

if __name__ == "__main__":
    import app.grpc_server
    app.grpc_server.serve()
