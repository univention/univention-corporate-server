from collections.abc import MutableMapping

from univention.management.console.session_db import DBSession


class SessionDict(MutableMapping):
    sessions = {}

    def __delitem__(self, key) -> None:
        DBSession.delete(key)
        del self.sessions[key]

    def __setitem__(self, key, value) -> None:
        session = DBSession.get(key)
        if session:
            DBSession.update(key, value)
        else:
            DBSession.create(key, value)

        self.sessions[key] = value

    def __getitem__(self, key):
        i = self.sessions[key]
        session = DBSession.get(key)
        if not session:
            del self.sessions[key]
            raise KeyError(key)
        return i

    def __len__(self) -> int:
        return len(self.sessions)

    def __iter__(self):
        return self.sessions.__iter__()

    def get_oidc_sessions(self, logout_token_claims):
        sessions = DBSession.get_by_oidc(logout_token_claims)
        return sessions
