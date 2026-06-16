import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlmodel import Session

from app.db.session import engine
from app.services.interaction_logging import evaluate_saved_rag_interactions


def main() -> None:
    with Session(engine) as session:
        created_count = evaluate_saved_rag_interactions(session)

    print(f"Created {created_count} groundedness evaluation logs.")


if __name__ == "__main__":
    main()

