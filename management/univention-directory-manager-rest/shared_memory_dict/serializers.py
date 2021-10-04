import json
import pickle

NULL_BYTE = b"\x00"


class SerializationError(ValueError):
    def __init__(self, data):
        super(SerializationError, self).__init__("Failed to serialize data: {data!r}".format(data=data))


class DeserializationError(ValueError):
    def __init__(self, data):
        super(DeserializationError, self).__init__("Failed to deserialize data: {data!r}".format(data=data))


class JSONSerializer:
    __slots__ = ()

    encoder = json.JSONEncoder
    decoder = json.JSONDecoder

    def dumps(self, obj):
        try:
            return json.dumps(obj, cls=self.encoder).encode() + NULL_BYTE
        except (ValueError, TypeError):
            raise SerializationError(obj)

    def loads(self, data):
        data = data.split(NULL_BYTE, 1)[0]
        try:
            return json.loads(data, cls=self.decoder)
        except json.JSONDecodeError:
            raise DeserializationError(data)


class PickleSerializer:
    def dumps(self, obj):
        try:
            return pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
        except pickle.PicklingError:
            raise SerializationError(obj)

    def loads(self, data):
        try:
            return pickle.loads(data)
        except pickle.UnpicklingError:
            raise DeserializationError(data)
