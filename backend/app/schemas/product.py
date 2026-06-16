from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductVariantSeed(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_sku: str
    color: str
    size: str
    stock: int
    price: Decimal


class ProductSeed(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: str
    title: str
    category: str
    description: str
    price: Decimal
    currency: str
    variants: list[ProductVariantSeed]


class ProductVariantRead(ProductVariantSeed):
    id: int
    product_id: int
    active: bool


class ProductRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    sku: str
    title: str
    category: str
    description: str
    price: Decimal
    currency: str
    active: bool
    variants: list[ProductVariantRead] = []

