from app.api.deps import get_ingestion_service


def main() -> None:
    result = get_ingestion_service().ingest_directory(clear_existing=False)
    print(result)


if __name__ == "__main__":
    main()
