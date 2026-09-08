import asyncio
import random

from src.core.payments.interfaces import PaymentGatewayProtocol

SUCCESS_PROBABILITY = 0.9
MIN_PROCESSING_SECONDS = 2.0
MAX_PROCESSING_SECONDS = 5.0


class PaymentGatewayEmulator(PaymentGatewayProtocol):
    """Эмуляция шлюза: задержка 2-5 сек, 90% успех / 10% отказ."""

    async def charge(self) -> bool:
        delay = random.uniform(MIN_PROCESSING_SECONDS, MAX_PROCESSING_SECONDS)
        await asyncio.sleep(delay)
        return random.random() < SUCCESS_PROBABILITY
