import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.scheduler import start_scheduler, stop_scheduler
from app.api.router import api_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("panopticon")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting PANOPTICON")
    start_scheduler()
    yield
    logger.info("Shutting down PANOPTICON")
    stop_scheduler()


app = FastAPI(title="PANOPTICON", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
