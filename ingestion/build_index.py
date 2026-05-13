from pathlib import Path

from app.api.deps import get_ingestion_service


def build_index(directory: str | Path | None = None, clear_existing: bool = False) -> dict:
    return get_ingestion_service().ingest_directory(
        directory=Path(directory) if directory else None,
        clear_existing=clear_existing,
    )
