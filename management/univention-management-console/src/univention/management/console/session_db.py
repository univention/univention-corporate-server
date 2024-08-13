import time
from contextlib import contextmanager

from sqlalchemy import BigInteger, Column, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from univention.config_registry import ucr


engine = create_engine(ucr['umc/http/session/db-url'])
Base = declarative_base()


@contextmanager
def get_session(bind, auto_commit=True):
    # type: (bool) -> Iterator[sqlalchemy.Session]
    session = None
    try:
        session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=bind))
        yield session
    finally:
        if session is not None:
            if auto_commit:
                session.commit()
            session.remove()
            session.bind.dispose()


class DBSession(Base):
    __tablename__ = 'sessions'
    session_id = Column(String, primary_key=True)
    expire_time = Column(BigInteger)
    oidc_sid = Column(String)
    oidc_sub = Column(String)
    oidc_iss = Column(String)

    sessions = {}

    def __repr__(self):
        return f'<Session(session_id={self.session_id}, expire_time={self.expire_time})>'

    @classmethod
    def get(cls, session_id):
        with get_session(bind=engine) as session:
            return session.query(cls).filter(cls.session_id == session_id).first()

    @classmethod
    def delete(cls, session_id):
        with get_session(bind=engine) as session:
            session.query(cls).filter(cls.session_id == session_id).delete()

    @classmethod
    def update(cls, session_id, value):
        with get_session(bind=engine) as session:
            expire_time = cls.calculate_session_end_time(value)
            session.query(cls).filter(cls.session_id == session_id).update({'expire_time': expire_time})
            session.commit()

    @classmethod
    def create(cls, session_id, umcSession):
        oidc_params = {}
        if umcSession.oidc:
            oidc_params['oidc_sid'] = umcSession.oidc.claims['sid']
            oidc_params['oidc_sub'] = umcSession.oidc.claims['sub']
            oidc_params['oidc_iss'] = umcSession.oidc.claims['iss']

        with get_session(bind=engine) as session:
            session.add(cls(session_id=session_id, expire_time=cls.calculate_session_end_time(umcSession), **oidc_params))
            session.commit()

    @classmethod
    def calculate_session_end_time(cls, value):
        session_valid_in_seconds = value.session_end_time - time.monotonic()
        real_session_end_time = time.time() + session_valid_in_seconds

        return real_session_end_time

    @classmethod
    def get_by_oidc(cls, claims):
        with get_session(bind=engine) as session:
            oidc_sessions_by_sid = session.query(cls).filter(cls.oidc_iss == claims.get('iss'), cls.oidc_sid == claims.get('sid')).first()
            if oidc_sessions_by_sid:
                yield oidc_sessions_by_sid
            else:
                oidc_sessions_by_sub = session.query(cls).filter(cls.oidc_iss == claims.get('iss'), cls.oidc_sub == claims.get('sub')).all()
                for oidc_session in oidc_sessions_by_sub:
                    yield oidc_session


Base.metadata.create_all(engine)
