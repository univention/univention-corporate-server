import os
import time
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import BigInteger, Column, String, create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from tornado import ioloop

import univention.debug as ud
from univention.management.console.config import SQL_CONNECTION_ENV_VAR
from univention.management.console.log import CORE
from univention.management.console.sse import logout_notifiers


class DBDisabledException(Exception):
    pass


class PostgresListenNotifyUnsupported(Exception):
    pass


Base = declarative_base()


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
        ud.debug(ud.MAIN, 99, "Connecting to database: %s" % (connection_uri,))
        engine = create_engine(connection_uri, pool_pre_ping=True)
        cls.__engine = engine
        cls.__registry = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        Base.metadata.create_all(cls.__engine)

        try:
            CORE.debug("Starting the PostgresListener")
            PostgresListener(engine).listen()
        except PostgresListenNotifyUnsupported as e:
            CORE.warning('The configured database is not Postgres. The automatic portal refresh will not work!\n%s', e)

        cls._enabled = True


class PostgresListener:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.conn = engine.connect()

    def verify_postgres(self, engine: Engine | None = None):
        if engine is None:
            engine = self.engine
        if not self.engine.dialect.dialect_description == 'postgresql+psycopg2':
            raise PostgresListenNotifyUnsupported(f"Expected sqlalchemy dialect 'pstgresql+psycopg' but got {self.engine.dialect.dialect_description}")

    def listen(self):
        self.verify_postgres()
        CORE.debug("Executing 'LISTEN logout'")
        self.conn.execution_options(autocommit=True).execute(text("LISTEN logout"))
        ioloop.IOLoop.current().asyncio_loop.add_reader(self.conn.connection, self.handle_postgres_notify)

    def handle_postgres_notify(self):
        if self.conn is None:
            return
        self.conn.connection.poll()
        while self.conn.connection.notifies:
            notify = self.conn.connection.notifies.pop()
            payload = notify.payload
            notifier = logout_notifiers.get(payload)
            if notifier is not None:
                CORE.debug('Got a logout notifier for session %s' % (payload))
                notifier.set()

    @classmethod
    def notify(cls, conn: Connection | Session, session_id: str):
        if isinstance(conn, Session):
            connection = conn.connection()
        else:
            connection = conn

        cls.verify_postgres(connection.engine)
        connection.execution_options(autocommit=True).execute(text("NOTIFY logout, :session_id;").bindparams(session_id=session_id))


@contextmanager
def get_session(auto_commit=True) -> Generator[Session, None, None]:
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
            session.close()


class DBSession(Base):
    __tablename__ = 'sessions'
    session_id = Column(String(256), primary_key=True)
    expire_time = Column(BigInteger)
    oidc_sid = Column(String(256))
    oidc_sub = Column(String(256))
    oidc_iss = Column(String(256))

    sessions = {}

    def __repr__(self):
        return f'<Session(session_id={self.session_id}, expire_time={self.expire_time}, oidc_sid={self.oidc_sid}, oidc_sub={self.oidc_sub}, oidc_iss={self.oidc_iss})>'

    @classmethod
    def get(cls, db_session, session_id):
        return db_session.query(cls).filter(cls.session_id == session_id).first()

    @classmethod
    def delete(cls, db_session: Session, session_id: str, send_postgres_logout_notify: bool = False):
        if send_postgres_logout_notify:
            try:
                CORE.debug("Deleting a session that is not ours. Sending postgres notify")
                PostgresListener.notify(db_session, session_id)
            except PostgresListenNotifyUnsupported:
                pass
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
            yield from oidc_sessions_by_sub
