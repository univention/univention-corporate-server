"""Public interface for test resultes."""

from __future__ import annotations

import warnings
from enum import Enum


__all__ = ['Reason']


class Reason(Enum):
    UNKNOWN = (-1, "E", "Test failed", "RED")
    SKIP = (77, "S", "Test skipped", "BLUE")
    OKAY = (100, "O", "Test passed", "GREEN")
    FIXED_EXPECTED = (101, "O", "Test passed", "GREEN")
    FIXED_UNEXPECTED = (102, "O", "Test passed", "GREEN")
    FAIL = (110, "F", "Test failed", "RED")
    FAIL_UNEXPECTED = (111, "F", "Test failed", "RED")
    FAIL_TRANSIENT = (120, "F", "Test failed", "RED")
    FAIL_EXPECTED = (121, "F", "Test failed", "RED")
    UNAVAILABLE = (122, "E", "Test failed", "RED")
    IMMATURE = (130, "S", "Test failed", "RED")
    VERSION_MISMATCH = (131, "S", "Test skipped (wrong version)", "BLUE")
    VERSION_TOO_OLD = (132, "S", "Test skipped (version too old)", "BLUE")
    VERSION_TOO_NEW = (133, "S", "Test skipped (version too new)", "BLUE")
    ROLE_MISMATCH = (134, "S", "Test skipped (role mismatch)", "BLUE")
    JOIN = (135, "S", "Test skipped (system not joined)", "BLUE")
    JOINED = (136, "S", "Test skipped (system is joined)", "BLUE")
    INSTALL = (137, "S", "Test skipped (missing software)", "BLUE")
    INSTALLED = (138, "S", "Test skipped (conflicting software)", "BLUE")
    DANGER = (139, "S", "Test skipped (too dangerous)", "BLUE")
    INTERNAL = (140, "E", "Test failed", "RED")
    ABORT = (141, "S", "Test aborted", "RED")
    APP_MISMATCH = (142, "S", "Test skipped (app mismatch)", "BLUE")

    def __int__(self) -> int:
        return self.value[0]

    @property
    def eofs(self) -> str:  # Error Okay Failure Skip
        return self.value[1]

    def __str__(self) -> str:
        return self.value[2]

    @property
    def color(self):
        return self.value[3]

    @classmethod
    def lookup(cls, code: int) -> Reason:
        return next(obj for obj in cls.__members__.values() if int(obj) == code)


MAX_MESSAGE_LEN: int = max((len(str(obj)) for obj in Reason.__members__.values()), default=0)


class _TestCodes:
    """Deprecated. Use :py:class:`Reason`."""

    RESULT_OKAY = 0
    RESULT_FAIL = 1
    RESULT_SKIP = 77

    MESSAGE = {int(reason): str(reason) for reason in Reason.__members__.values()}
    MAX_MESSAGE_LEN = MAX_MESSAGE_LEN
    COLOR = {int(reason): reason.color for reason in Reason.__members__.values()}
    EOFS = {
        0: "O",
        1: "F",
        **{int(reason): reason.eofs for reason in Reason.__members__.values()},
    }

    def __getattribute__(self, item: str):
        warnings.warn(f"deprecated use of TestCodes.{item}", DeprecationWarning, stacklevel=2)
        if item.startswith("REASON_"):
            return int(getattr(Reason, item[7:]))
        return object.__getattribute__(self, item)


TestCodes = _TestCodes()
