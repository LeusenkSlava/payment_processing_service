import asyncio
import logging

from src.inbound.rabbit_mq.handlers import register_handlers
from src.main.config.logging import setup_logging
from src.outbound.database.session import engine
from src.outbound.rabbit_mq.broker import broker, setup_topology
from src.outbound.webhook.client import http_client

logger = logging.getLogger(__name__)


async def main() -> None:
    setup_logging()
    await broker.connect()
    await setup_topology()
    register_handlers()

    await broker.start()

    logger.info("Consumer started, waiting for messages...")

    try:
        await asyncio.Event().wait()
    finally:
        await http_client.aclose()
        await broker.stop()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
