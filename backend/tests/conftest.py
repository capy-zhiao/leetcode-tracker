"""Test fixtures: each test gets its own in-memory database."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Problem, ReviewState


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",                       # in-memory
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,              # share one database across connections
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_problems(db_session):
    """Three problems: one never attempted, two solved and due for review."""
    from datetime import date, timedelta
    today = date.today()
    rows = [
        Problem(number=1, title="Two Sum", difficulty="Easy", chapter_num=1,
                chapter="Arrays & Hashing", url="", kind="problem"),
        Problem(number=994, title="Rotting Oranges", difficulty="Medium", chapter_num=11,
                chapter="Graphs", url="", kind="problem"),
        Problem(number=200, title="Number of Islands", difficulty="Medium", chapter_num=11,
                chapter="Graphs", url="", kind="problem"),
    ]
    db_session.add_all(rows)
    db_session.flush()
    # 994 is five days overdue and has failed three times -> highest priority
    db_session.add(ReviewState(problem_id=rows[1].id, interval_days=2, reps=1,
                               lapses=3, due=today - timedelta(days=5)))
    db_session.add(ReviewState(problem_id=rows[2].id, interval_days=4, reps=2,
                               lapses=0, due=today))
    db_session.commit()
    return rows
