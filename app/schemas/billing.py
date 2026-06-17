from pydantic import BaseModel, Field, model_validator

from app.core.config import settings


class PaymentCreateRequest(BaseModel):
    tokens: int | None = Field(default=None, ge=1, description="Tokens to credit on success")
    amount: int | None = Field(default=None, ge=1, description="Payment amount in minor units")

    @model_validator(mode="after")
    def validate_order_limits(self) -> "PaymentCreateRequest":
        cap = settings.simulated_recharge_amount
        if self.tokens is not None and self.tokens > cap:
            raise ValueError(f"tokens must not exceed {cap}")
        if self.amount is not None and self.amount > cap:
            raise ValueError(f"amount must not exceed {cap}")
        return self


class PaymentResponse(BaseModel):
    id: str
    user_id: str
    amount: int
    tokens: int
    status: str
    created_at: str | None = None
    token_balance: int | None = None
