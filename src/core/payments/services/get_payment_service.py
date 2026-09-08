from src.core.payments.exceptions import PaymentNotFoundError
from src.core.payments.interfaces import PaymentRepositoryProtocol
from src.core.payments.models.payment import Payment


class GetPaymentService:
    """Возвращает платёж"""

    def __init__(self, payment_repo: PaymentRepositoryProtocol) -> None:
        self._payment_repo = payment_repo

    async def get(self, payment_id: int) -> Payment:
        """Возвращает платёж по id.

        :param payment_id: id платежа.
        :return: найденный платёж.
        :raises PaymentNotFoundError: если платёж не найден.
        """
        payment = await self._payment_repo.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError(payment_id)
        return payment
