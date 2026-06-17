import sys
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import app.models  # noqa: F401
from scripts.seed_database import seed_orders, seed_products


@pytest.fixture()
def test_session(tmp_path: Path) -> Session:
    engine = create_engine(f"sqlite:///{tmp_path / 'shopguard_test.db'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_products(session)
        seed_orders(session)
        session.commit()
        yield session

