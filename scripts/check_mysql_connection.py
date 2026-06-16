from pathlib import Path
import sys

from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    with engine.connect() as connection:
        database_name = connection.scalar(text("SELECT DATABASE()"))
        server_version = connection.scalar(text("SELECT VERSION()"))

    print("MySQL connection successful")
    print(f"Database: {database_name}")
    print(f"Server version: {server_version}")


if __name__ == "__main__":
    main()
