import datetime

from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table


metadata_obj = MetaData()

state_table = Table(
    "state",
    metadata_obj,
    Column('state', String(300), primary_key=True),
    Column('code_verifier', String(255), nullable=False),
    Column('redirect_uri', String(2048), nullable=False),
    Column('expires', DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now() + datetime.timedelta(minutes=5), index=True),
)

session_table = Table(
    "sessions",
    metadata_obj,
    Column('session_id', String(300), primary_key=True, index=True),
    Column('id_token', String(2048), nullable=False),
    Column('access_token', String(2048), nullable=False),
    Column('refresh_token', String(2048), nullable=False),
    Column('refresh_expires_in', Integer, nullable=False),
    Column('access_expires_in', Integer, nullable=False),
    Column('uid', String(255), nullable=False),
    Column('umc_access_token', String(2048), nullable=False),
    Column('sub', String(255), nullable=False, index=True),
    Column('sid', String(255), nullable=False, index=True),
    Column('iss', String(255), nullable=False, index=True),
    Column('created_at', DateTime(timezone=True), nullable=False),
    Column('refresh_expires_at', DateTime(timezone=True), nullable=False, index=True),
    Column('access_expires_at', DateTime(timezone=True), nullable=False),
)
