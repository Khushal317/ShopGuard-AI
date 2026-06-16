import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.knowledge_ingestion import ingest_knowledge_base


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the local ChromaDB knowledge collection.")
    parser.add_argument("--no-rebuild", action="store_true", help="Keep the existing collection data.")
    args = parser.parse_args()

    summary = ingest_knowledge_base(rebuild=not args.no_rebuild)
    print(summary.model_dump_json())


if __name__ == "__main__":
    main()

