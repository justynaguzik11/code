# pylint: disable=attribute-defined-outside-init
from __future__ import annotations
import abc
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from src.allocation import config
from src.allocation.adapters import repository


class AbstractUnitOfWork(abc.ABC):
    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError


DEFAULT_SESSION_FACTORY = sessionmaker(
    bind=create_engine(
        config.get_postgres_uri(),
    )
)


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory
        self.session = None
        self.batches = None

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()


class UnitOfWorkManager:
    def __init__(self, uov: SqlAlchemyUnitOfWork):
        self.uov = uov

    def __enter__(self):
        self.uov.session = self.uov.session_factory()
        self.uov.batches = repository.SqlAlchemyRepository(self.uov.session)
        return self.uov

    def __exit__(self, *args):
        self.uov.rollback()
        self.uov.session.close()


# One alternative would be to define a `start_uow` function,
# or a UnitOfWorkStarter or UnitOfWorkManager that does the
# job of context manager, leaving the UoW as a separate class
# that's returned by the context manager's __enter__.
#
# A type like this could work?
# AbstractUnitOfWorkStarter = ContextManager[AbstractUnitOfWork]
