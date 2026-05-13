from pathlib import Path

from app.services.document_loader import DocumentLoader, LoadedDocument


def parse_pdf(path: str | Path) -> list[LoadedDocument]:
    return DocumentLoader().load_file(Path(path))
