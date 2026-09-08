from fastapi import APIRouter, Depends, Header, HTTPException

from src.core.payments.exceptions import PaymentNotFoundError
from src.core.payments.services.create_payment import CreatePaymentService
from src.core.payments.services.get_payment_service import GetPaymentService
from src.inbound.http.dependencies.auth import verify_api_key
from src.inbound.http.payments.dependencies import (
    get_create_payment_service,
    get_get_payment_service,
)
from src.inbound.http.payments.schemas import (
    PaymentCreateRequest,
    PaymentDetailResponse,
    PaymentResponse,
)

router = APIRouter(
    tags=["Payments"],
    prefix="/api/v1",
    dependencies=[Depends(verify_api_key)],
)


@router.post(
    "/payments",
    status_code=202,
    response_model=PaymentResponse,
    summary="Создать платёж",
)
async def create_payment(
    data: PaymentCreateRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    service: CreatePaymentService = Depends(get_create_payment_service),
):
    """
    Создаёт платёж и ставит событие о нём в очередь на обработку.

    Идемпотентно по заголовку Idempotency-Key: повторный запрос с тем же
    ключом вернёт уже существующий платёж вместо создания дубля.
    """
    payment = await service.execute(data, idempotency_key)
    return PaymentResponse(
        payment_id=payment.id,
        status=payment.status,
        created_at=payment.created_at,
    )


@router.get(
    "/payments/{payment_id}",
    response_model=PaymentDetailResponse,
    summary="Получить платёж по id",
    responses={404: {"description": "Payment '{payment_id}' not found"}},
)
async def get_payment(
    payment_id: int,
    service: GetPaymentService = Depends(get_get_payment_service),
):
    """
    Возвращает детальную информацию о платеже.

    :param payment_id: id платежа.
    :raises HTTPException: 404, если платёж не найден.
    """
    try:
        payment = await service.get(payment_id)
    except PaymentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Payment {payment_id} not found")

    return PaymentDetailResponse(
        idempotency_key=payment.idempotency_key,
        id=payment.id,
        created_at=payment.created_at,
        processed_at=payment.processed_at,
        amount=payment.amount,
        currency=payment.currency,
        webhook_url=payment.webhook_url,
        description=payment.description,
        meta_data=payment.meta_data,
        status=payment.status,
    )
