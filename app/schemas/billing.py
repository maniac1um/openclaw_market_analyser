from pydantic import BaseModel, Field


class PaymentCreateRequest(BaseModel):
    tokens: int | None = Field(default=None, ge=1, description="Tokens to credit on success")
    amount: int | None = Field(default=None, ge=1, description="Payment amount in minor units")


class PaymentResponse(BaseModel):
    id: str
    user_id: str
    amount: int
    tokens: int
    status: str
    created_at: str | None = None
    token_balance: int | None = None
