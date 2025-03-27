#!/usr/bin/python3
#
# Univention Management Console
#  OpenID Connect implementation for the Portal
#
# Copyright 2025 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.
import asyncio
import datetime
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from sqlalchemy import and_, delete, select
from sqlalchemy.exc import InterfaceError
from sqlalchemy.ext.asyncio import AsyncConnection

from univention.portal.extensions.oidc.auth import TokenResponse
from univention.portal.extensions.oidc.schema import session_table, state_table
from univention.portal.log import get_logger


async def cleanup(engine_provider):
    get_logger('user').debug('starting cleanup task')
    while True:
        get_logger('user').debug('cleanup task sleeping 30 seconds')
        await asyncio.sleep(30)
        async with engine_provider() as conn, conn.begin():
            try:
                now = datetime.datetime.now(datetime.UTC)
                await conn.execute(delete(state_table).where(state_table.c.expires < now))
                await conn.execute(delete(session_table).where(session_table.c.refresh_expires_at < now))
            except asyncio.CancelledError:
                raise
            except Exception:
                raise


@dataclass
class OIDCSession:
    id_token: str
    access_token: str
    refresh_token: str
    refresh_expires_in: int
    access_expires_in: int
    created_at: datetime.datetime
    uid: str
    umc_access_token: str
    sub: str
    sid: str
    iss: str
    refresh_expires_at: datetime.datetime
    access_expires_at: datetime.datetime

    @classmethod
    def from_token_response(cls, resp: TokenResponse, verify_func: Callable[[str], dict[str, Any]]):
        id_token = resp.id_token
        verified_id_token = verify_func(id_token)

        created_at = datetime.datetime.now(datetime.UTC)

        refresh_expires_in = resp.refresh_expires_in
        access_expires_in = resp.expires_in
        return OIDCSession(
            id_token=id_token,
            access_token=resp.access_token,
            refresh_token=resp.refresh_token,
            refresh_expires_in=refresh_expires_in,
            access_expires_in=access_expires_in,
            uid=verified_id_token['uid'],
            umc_access_token="",
            created_at=created_at,
            refresh_expires_at=created_at + datetime.timedelta(seconds=refresh_expires_in),
            access_expires_at=created_at + datetime.timedelta(seconds=access_expires_in),
            sub=verified_id_token['sub'],
            sid=verified_id_token['sid'],
            iss=verified_id_token['iss'],
        )


class DatabaseError(Exception):
    msg = "Database operation failed: {0}"

    def __init__(self, error: str) -> None:
        super().__init__(self.msg.format(error))


class BaseRepository:
    def __init__(self, engine_provider) -> None:
        self.engine_provider = engine_provider

    @asynccontextmanager
    async def db_transaction(self) -> AsyncGenerator[AsyncConnection, None]:
        try:
            async with self.engine_provider() as conn:
                async with conn.begin():
                    yield conn
        except ConnectionRefusedError as err:
            raise DatabaseError("Failed to connect to database") from err
        except InterfaceError as err:
            raise DatabaseError("Database connection error") from err


class SessionRepository(BaseRepository):
    def __init__(self, engine_provider) -> None:
        super().__init__(engine_provider)
        self.engine_provider = engine_provider

    async def create(self, session_id: str, session: OIDCSession):
        stmt = session_table.insert().values(
            session_id=session_id,
            id_token=session.id_token,
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            refresh_expires_in=session.refresh_expires_in,
            access_expires_in=session.access_expires_in,
            uid=session.uid,
            umc_access_token=session.umc_access_token,
            sub=session.sub,
            sid=session.sid,
            iss=session.iss,
            created_at=session.created_at,
            refresh_expires_at=session.refresh_expires_at,
            access_expires_at=session.access_expires_at,
        )
        async with self.db_transaction() as conn:
            await conn.execute(stmt)

    async def update(self, session_id: str, session: OIDCSession):
        stmt = session_table.update().where(session_table.c.session_id == session_id).values(
            session_id=session_id,
            id_token=session.id_token,
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            refresh_expires_in=session.refresh_expires_in,
            access_expires_in=session.access_expires_in,
            uid=session.uid,
            umc_access_token=session.umc_access_token,
            sub=session.sub,
            sid=session.sid,
            iss=session.iss,
            created_at=session.created_at,
            refresh_expires_at=session.refresh_expires_at,
            access_expires_at=session.access_expires_at,
        )
        async with self.db_transaction() as conn:
            await conn.execute(stmt)

    async def delete(self, session_id: str):
        async with self.db_transaction() as conn:
            await conn.execute(delete(session_table).where(session_table.c.session_id == session_id))

    async def find_by_session_id(self, session_id: str):
        stmt = select(
            session_table.c.id_token,
            session_table.c.access_token,
            session_table.c.refresh_token,
            session_table.c.refresh_expires_in,
            session_table.c.access_expires_in,
            session_table.c.created_at,
            session_table.c.uid,
            session_table.c.umc_access_token,
            session_table.c.sub,
            session_table.c.sid,
            session_table.c.iss,
            session_table.c.refresh_expires_at,
            session_table.c.access_expires_at,
        ).where(session_table.c.session_id == session_id)

        async with self.db_transaction() as conn:
            result = await conn.execute(stmt)
            row = result.fetchone()

        if row is None:
            return None

        return OIDCSession(**row)

    async def delte_by_iss_and_sub(self, iss: str, sub: str):
        async with self.db_transaction() as conn:
            await conn.execute(delete(session_table).where(and_(session_table.c.sub == sub, session_table.c.iss == iss)))

    async def delete_by_sid(self, sid: str):
        async with self.db_transaction() as conn:
            await conn.execute(delete(session_table).where(session_table.c.sid == sid))


class StateRepository(BaseRepository):
    def __init__(self, engine_provider) -> None:
        super().__init__(engine_provider)
        self.engine_provider = engine_provider

    async def create(self, state: str, code_verifier: str, redirect_uri: str):
        stmt = state_table.insert().values(
            state=state,
            code_verifier=code_verifier,
            redirect_uri=redirect_uri,
        )
        async with self.db_transaction() as conn:
            await conn.execute(stmt)

    async def get_and_delete(self, state: str) -> dict[str, Any] | None:
        async with self.db_transaction() as conn:
            stmt = select(state_table).where(state_table.c.state == state)
            res = (await conn.execute(stmt)).fetchone()
            if res is None:
                return None
            await conn.execute(delete(state_table).where(state_table.c.state == state))
        return res
