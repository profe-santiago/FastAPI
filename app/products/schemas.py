from pydantic import BaseModel, Field
from datetime import datetime


class ProductCreate(BaseModel):
    name:        str   = Field(..., min_length=1, max_length=200)
    description: str   = Field("", max_length=500)
    price:       float = Field(..., gt=0)
    stock:       int   = Field(0, ge=0)


class ProductUpdate(BaseModel):
    name:        str | None   = Field(None, min_length=1, max_length=200)
    description: str | None   = Field(None, max_length=500)
    price:       float | None = Field(None, gt=0)
    stock:       int | None   = Field(None, ge=0)
    is_active:   bool | None  = None


class ProductResponse(BaseModel):
    id:          int
    name:        str
    description: str
    price:       float
    stock:       int
    is_active:   bool
    created_at:  datetime

    model_config = {"from_attributes": True}
