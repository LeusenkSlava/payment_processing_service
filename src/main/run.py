from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.inbound.http.root_router import make_fastapi_root_router
from src.main.config.logging import setup_logging
from src.main.config.settings import settings
from src.main.setup.background_tasks import BackgroundTaskRunner
from src.outbound.database.session import engine
from src.outbound.rabbit_mq.broker import broker, setup_topology
from src.outbound.webhook.client import http_client
from src.outbound.workers import BACKGROUND_WORKERS

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.connect()
    await setup_topology()

    background_tasks = BackgroundTaskRunner()
    background_tasks.start_all(BACKGROUND_WORKERS)

    yield

    await background_tasks.shutdown()
    await http_client.aclose()
    await broker.stop()
    await engine.dispose()


app = FastAPI(
    title=settings.app.SERVICE_NAME,
    version="1.0.0",
    summary=f"OpenAPI schema for {settings.app.SERVICE_NAME}",
    root_path=settings.app.ROOT_PATH.rstrip("/"),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(make_fastapi_root_router(debug_mode=settings.app.DEBUG_MODE))
