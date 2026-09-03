from fastapi import APIRouter, Depends, Header

from src.core.payments.services import CreatePaymentService
from src.inbound.http.payments.dependencies import get_create_payment_service
from src.inbound.http.payments.schemas import PaymentCreateRequest, PaymentResponse

router = APIRouter(tags=["Payments"], prefix="/api/v1")


@router.post("/payments", status_code=202, response_model=PaymentResponse)
async def create_payment(
    data: PaymentCreateRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    service: CreatePaymentService = Depends(get_create_payment_service),
):
    payment = await service.execute(data, idempotency_key)
    return PaymentResponse(payment_id=payment.id, status=payment.status)
