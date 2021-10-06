import json
import pickle
from typing import Final, Protocol

NULL_BYTE: Final = b"\x00"


class SerializationError(ValueError):
    def __init__(self, data: dict) -> None:
        super().__init__(f"Failed to serialize data: {data!r}")


class DeserializationError(ValueError):
    def __init__(self, data: bytes) -> None:
        super().__init__(f"Failed to deserialize data: {data!r}")


class SharedMemoryDictSerializer(Protocol):
    def dumps(self, obj: dict) -> bytes:
        ...

    def loads(self, data: bytes) -> dict:
        ...


class JSONSerializer:
    def dumps(self, obj: dict) -> bytes:
        try:
            return json.dumps(obj).encode() + NULL_BYTE
        except (ValueError, TypeError):
            raise SerializationError(obj)

    def loads(self, data: bytes) -> dict:
        data = data.split(NULL_BYTE, 1)[0]
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            raise DeserializationError(data)


class PickleSerializer:
    def dumps(self, obj: dict) -> bytes:
        try:
            return pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
        except pickle.PicklingError:
            raise SerializationError(obj)

    def loads(self, data: bytes) -> dict:
        try:
            return pickle.loads(data)
        except pickle.UnpicklingError:
            raise DeserializationError(data)
