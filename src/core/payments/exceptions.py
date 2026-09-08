class DuplicateIdempotencyKeyError(Exception):
    def __init__(self, idempotency_key: str) -> None:
        self.idempotency_key = idempotency_key
        super().__init__(
            f"Payment with idempotency_key={idempotency_key!r} already exists"
        )


class PaymentNotFoundError(Exception):
    def __init__(self, payment_id: int) -> None:
        self.payment_id = payment_id
        super().__init__(f"Payment with id={payment_id} not found")


class PaymentLockedError(Exception):
    def __init__(self, payment_id: int) -> None:
        self.payment_id = payment_id
        super().__init__(f"Payment {payment_id} is locked (processing) elsewhere")
