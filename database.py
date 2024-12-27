import contextlib

from sqlalchemy.orm import Session

from models import Base, SessionLocal, engine


def init_db():
    Base.metadata.create_all(bind=engine)

@contextlib.contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()