# Copyright 2020 LuizaLabs
# MIT License
# https://github.com/luizalabs/shared-memory-dict/

import logging
import sys
import warnings
from contextlib import contextmanager
from functools import wraps
from multiprocessing import Lock
from multiprocessing_shared_memory import SharedMemory
from typing import (
    Any,
    Dict,
    Generator,
    ItemsView,
    Iterator,
    KeysView,
    Optional,
    ValuesView,
)

from .serializers import PickleSerializer, SharedMemoryDictSerializer

MEMORY_NAME = 'sm_{name}'
NOT_GIVEN = object()
DEFAULT_SERIALIZER = PickleSerializer()


logger = logging.getLogger(__name__)

_lock = Lock()


def lock(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        _lock.acquire()
        try:
            return func(*args, **kwargs)
        finally:
            _lock.release()

    return wrapper


class SharedMemoryDict:
    def __init__(
        self,
        name: str,
        size: int,
        *,
        serializer: SharedMemoryDictSerializer = DEFAULT_SERIALIZER,
    ) -> None:
        super().__init__()
        self._serializer = serializer
        self._memory_block = self._get_or_create_memory_block(
            MEMORY_NAME.format(name=name), size
        )

    def cleanup(self) -> None:
        if not hasattr(self, '_memory_block'):
            return
        self._memory_block.close()

    def move_to_end(self, key: str, last: Optional[bool] = True) -> None:
        warnings.warn(
            'The \'move_to_end\' method will be removed in future versions. '
            'Use pop and reassignment instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        with self._modify_db() as db:
            db[key] = db.pop(key)

    @lock
    def clear(self) -> None:
        self._save_memory({})

    def popitem(self, last: Optional[bool] = None) -> Any:
        if last is not None:
            warnings.warn(
                'The \'last\' parameter will be removed in future versions. '
                'The \'popitem\' function now always returns last inserted.',
                DeprecationWarning,
                stacklevel=2,
            )
        with self._modify_db() as db:
            return db.popitem()

    @contextmanager
    @lock
    def _modify_db(self) -> Generator:
        db = self._read_memory()
        yield db
        self._save_memory(db)

    def __getitem__(self, key: str) -> Any:
        return self._read_memory()[key]

    def __setitem__(self, key: str, value: Any) -> None:
        with self._modify_db() as db:
            db[key] = value

    def __len__(self) -> int:
        return len(self._read_memory())

    def __delitem__(self, key: str) -> None:
        with self._modify_db() as db:
            del db[key]

    def __iter__(self) -> Iterator:
        return iter(self._read_memory())

    def __reversed__(self):
        return reversed(self._read_memory())

    def __del__(self) -> None:
        self.cleanup()

    def __contains__(self, key: str) -> bool:
        return key in self._read_memory()

    def __eq__(self, other: Any) -> bool:
        return self._read_memory() == other

    def __ne__(self, other: Any) -> bool:
        return self._read_memory() != other

    if sys.version_info > (3, 8):

        def __or__(self, other: Any):
            return self._read_memory() | other

        def __ror__(self, other: Any):
            return other | self._read_memory()

        def __ior__(self, other: Any):
            with self._modify_db() as db:
                db |= other
                return db

    def __str__(self) -> str:
        return str(self._read_memory())

    def __repr__(self) -> str:
        return repr(self._read_memory())

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self._read_memory().get(key, default)

    def keys(self) -> KeysView[Any]:
        return self._read_memory().keys()

    def values(self) -> ValuesView[Any]:
        return self._read_memory().values()

    def items(self) -> ItemsView:
        return self._read_memory().items()

    def pop(self, key: str, default: Optional[Any] = NOT_GIVEN):
        with self._modify_db() as db:
            if default is NOT_GIVEN:
                return db.pop(key)
            return db.pop(key, default)

    def update(self, other=(), /, **kwds):
        with self._modify_db() as db:
            db.update(other, **kwds)

    def setdefault(self, key: str, default: Optional[Any] = None):
        with self._modify_db() as db:
            return db.setdefault(key, default)

    def _get_or_create_memory_block(
        self, name: str, size: int
    ) -> SharedMemory:
        try:
            return SharedMemory(name=name)
        except FileNotFoundError:
            shm = SharedMemory(name=name, create=True, size=size)
            data = self._serializer.dumps({})
            shm.buf[: len(data)] = data
            return shm

    def _save_memory(self, db: Dict[str, Any]) -> None:
        data = self._serializer.dumps(db)
        try:
            self._memory_block.buf[: len(data)] = data
        except ValueError as exc:
            raise ValueError("exceeds available storage") from exc

    def _read_memory(self) -> Dict[str, Any]:
        return self._serializer.loads(self._memory_block.buf.tobytes())

    @property
    def shm(self) -> SharedMemory:
        return self._memory_block
