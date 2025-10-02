from sqlalchemy.engine import Engine
from .base import Base


def init_db(engine: Engine) -> None:
    from . import tables  # noqa: F401

    Base.metadata.create_all(bind=engine)
