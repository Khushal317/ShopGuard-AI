import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlmodel import Session, select

from app.db.session import engine, init_db
from app.models.order import Order, OrderItem
from app.models.product import Product, ProductVariant
from app.schemas.order import OrderSeed
from app.schemas.product import ProductSeed

DATA_DIR = ROOT_DIR / "data" / "mock_shopify"


def load_json(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def seed_products(session: Session) -> int:
    count = 0
    for raw_product in load_json(DATA_DIR / "products.json"):
        product_seed = ProductSeed.model_validate(raw_product)
        product = session.exec(select(Product).where(Product.sku == product_seed.sku)).first()

        if product is None:
            product = Product(
                sku=product_seed.sku,
                title=product_seed.title,
                category=product_seed.category,
                description=product_seed.description,
                price=product_seed.price,
                currency=product_seed.currency,
            )
            session.add(product)
            session.flush()
        else:
            product.title = product_seed.title
            product.category = product_seed.category
            product.description = product_seed.description
            product.price = product_seed.price
            product.currency = product_seed.currency
            product.active = True

        for variant_seed in product_seed.variants:
            variant = session.exec(
                select(ProductVariant).where(ProductVariant.variant_sku == variant_seed.variant_sku)
            ).first()

            if variant is None:
                variant = ProductVariant(
                    product_id=product.id,
                    variant_sku=variant_seed.variant_sku,
                    color=variant_seed.color,
                    size=variant_seed.size,
                    stock=variant_seed.stock,
                    price=variant_seed.price,
                )
                session.add(variant)
            else:
                variant.product_id = product.id
                variant.color = variant_seed.color
                variant.size = variant_seed.size
                variant.stock = variant_seed.stock
                variant.price = variant_seed.price
                variant.active = True

        count += 1

    return count


def seed_orders(session: Session) -> int:
    count = 0
    for raw_order in load_json(DATA_DIR / "orders.json"):
        order_seed = OrderSeed.model_validate(raw_order)
        order = session.exec(select(Order).where(Order.order_id == order_seed.order_id)).first()

        if order is None:
            order = Order(
                order_id=order_seed.order_id,
                customer_email=str(order_seed.customer_email),
                customer_name=order_seed.customer_name,
                status=order_seed.status,
                refund_status=order_seed.refund_status,
                total_amount=order_seed.total_amount,
                currency=order_seed.currency,
                tracking_number=order_seed.tracking_number,
            )
            session.add(order)
            session.flush()
        else:
            order.customer_email = str(order_seed.customer_email)
            order.customer_name = order_seed.customer_name
            order.status = order_seed.status
            order.refund_status = order_seed.refund_status
            order.total_amount = order_seed.total_amount
            order.currency = order_seed.currency
            order.tracking_number = order_seed.tracking_number

        existing_items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
        for item in existing_items:
            session.delete(item)
        session.flush()

        for item_seed in order_seed.items:
            session.add(
                OrderItem(
                    order_id=order.id,
                    product_sku=item_seed.product_sku,
                    variant_sku=item_seed.variant_sku,
                    title=item_seed.title,
                    quantity=item_seed.quantity,
                    unit_price=item_seed.unit_price,
                )
            )

        count += 1

    return count


def main() -> None:
    init_db()
    with Session(engine) as session:
        product_count = seed_products(session)
        order_count = seed_orders(session)
        session.commit()

    print(f"Seeded {product_count} products and {order_count} orders.")


if __name__ == "__main__":
    main()

