from pydantic import BaseModel, Field


class UserBalanceResponse(BaseModel):
    balance: int = Field(description="total_grants - total_usage")
    total_grants: int
    total_usage: int
