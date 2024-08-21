import os
import time
from contextlib import contextmanager

from sqlalchemy import BigInteger, Column, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from .config import SQL_CONNECTION_ENV_VAR


class DBDisabledException(Exception):
    pass


class DBRegistry:
    __engine = None
    __registry = None
    __init = False
    _enabled = False

    @classmethod
    def get(cls):
        if not cls.__init:
            cls.__create()

        return cls.__registry()

    @classmethod
    def enabled(cls):
        if not cls.__init:
            cls.__create()

        return cls._enabled

    @classmethod
    def __create(cls):
        cls.__init = True
        connection_uri = os.environ.get(SQL_CONNECTION_ENV_VAR, None)
        if connection_uri is None:
            return

        engine = create_engine(connection_uri)
        cls.__engine = engine
        cls.__registry = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
        Base.metadata.create_all(cls.__engine)
        cls._enabled = True


Base = declarative_base()


@contextmanager
def get_session(auto_commit=True):
    # type: (bool) -> Iterator[sqlalchemy.Session]
    if not DBRegistry.enabled():
        raise DBDisabledException

    session = None
    try:
        session = DBRegistry.get()
        yield session
    finally:
        if session is not None:
            if auto_commit:
                session.commit()


class DBSession(Base):
    __tablename__ = 'sessions'
    session_id = Column(String, primary_key=True)
    expire_time = Column(BigInteger)
    oidc_sid = Column(String)
    oidc_sub = Column(String)
    oidc_iss = Column(String)

    sessions = {}

    def __repr__(self):
        return f'<Session(session_id={self.session_id}, expire_time={self.expire_time}, oidc_sid={self.oidc_sid}, oidc_sub={self.oidc_sub}, oidc_iss={self.oidc_iss})>'

    @classmethod
    def get(cls, db_session, session_id):
        return db_session.query(cls).filter(cls.session_id == session_id).first()

    @classmethod
    def delete(cls, db_session, session_id):
        db_session.query(cls).filter(cls.session_id == session_id).delete()

    @classmethod
    def update(cls, db_session, session_id, umc_session):
        expire_time = cls.calculate_session_end_time(umc_session)
        db_session.query(cls).filter(cls.session_id == session_id).update({'expire_time': expire_time})

    @classmethod
    def create(cls, db_session, session_id, umc_session):
        oidc_params = {}
        if umc_session.oidc:
            oidc_params['oidc_sid'] = umc_session.oidc.claims.get('sid')
            oidc_params['oidc_sub'] = umc_session.oidc.claims.get('sub')
            oidc_params['oidc_iss'] = umc_session.oidc.claims.get('iss')

        db_session.add(cls(session_id=session_id, expire_time=cls.calculate_session_end_time(umc_session), **oidc_params))
        db_session.commit()

    @classmethod
    def calculate_session_end_time(cls, umc_session):
        session_valid_in_seconds = umc_session.session_end_time - time.monotonic()
        real_session_end_time = time.time() + session_valid_in_seconds

        return real_session_end_time

    @classmethod
    def get_by_oidc(cls, db_session, claims):
        oidc_sessions_by_sid = db_session.query(cls).filter(cls.oidc_iss == claims.get('iss'), cls.oidc_sid == claims.get('sid')).first()
        if oidc_sessions_by_sid:
            yield oidc_sessions_by_sid
        else:
            oidc_sessions_by_sub = db_session.query(cls).filter(cls.oidc_iss == claims.get('iss'), cls.oidc_sub == claims.get('sub')).all()
            for oidc_session in oidc_sessions_by_sub:
                yield oidc_session
