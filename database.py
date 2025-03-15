import contextlib

from sqlalchemy.orm import Session

from models import Base, SessionLocal, engine, init_triggers  # Import init_triggers


def init_db():
    Base.metadata.create_all(bind=engine)
    init_triggers()  # Initialize the Bayesian rating trigger

@contextlib.contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()