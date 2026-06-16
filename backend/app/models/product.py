from decimal import Decimal

from sqlmodel import Field, Relationship, SQLModel


class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    sku: str = Field(index=True, unique=True)
    title: str
    category: str
    description: str
    price: Decimal = Field(max_digits=10, decimal_places=2)
    currency: str = "USD"
    active: bool = True

    variants: list["ProductVariant"] = Relationship(back_populates="product")


class ProductVariant(SQLModel, table=True):
    __tablename__ = "product_variants"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    variant_sku: str = Field(index=True, unique=True)
    color: str
    size: str
    stock: int
    price: Decimal = Field(max_digits=10, decimal_places=2)
    active: bool = True

    product: Product = Relationship(back_populates="variants")

