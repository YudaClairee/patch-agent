from sqlmodel import create_engine, Session
from src.core.config import settings

engine = create_engine(settings.database_url, echo=(settings.environment == "development"))


def get_session():
    with Session(engine) as session:
        yield session
