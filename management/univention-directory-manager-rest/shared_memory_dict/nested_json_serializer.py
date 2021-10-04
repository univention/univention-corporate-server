import json

try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping

from shared_memory_dict.dict import SharedMemoryDict
from shared_memory_dict.serializers import JSONSerializer

json_serializer = JSONSerializer()
__shared_memory = {}


class JsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, DictProxy):
            return o.__dict__
        elif isinstance(o, SharedMemoryDict):
            return dict(o)
        raise TypeError(
            'Object of type {} is not JSON serializable'.format(
                type(o).__name__
            )
        )


class JsonDecoder(json.JSONDecoder):
    def decode(self, s):
        data = super(JsonDecoder, self).decode(s)
        assert isinstance(data, dict)
        return data


class DictProxy(MutableMapping):

    __slots__ = ('root', 'tree', '__dict__')

    @classmethod
    def from_shared_memory_dict(cls, root, tree, data):
        smd = SharedMemoryDict(
            root.name, root.shm.size, serializer=json_serializer
        )
        smd.name = root.name
        self = cls(smd, tree)
        self.__dict__ = data
        return self

    def __init__(self, root, tree, *args, **kwargs):
        self.root = root
        self.tree = tree
        self.update(*args, **kwargs)

    def parent(self, root=None):
        parent = root if root is not None else self.root
        for ekey in self.tree:
            parent = parent[ekey]
        return parent

    def reload_cache(self):
        data = self.parent()
        self.__dict__.clear()
        self.__dict__.update(data)

    def __setitem__(self, key, value):
        with self.root._modify_db() as root:
            self.__dict__[key] = value
            self.parent(root)[key] = value

    def __getitem__(self, key):
        self.reload_cache()
        value = self.__dict__[key]
        if isinstance(value, dict):
            return self.from_shared_memory_dict(
                self.root, tuple(list(self.tree) + [key]), value
            )
        return value

    def __delitem__(self, key):
        with self.root._modify_db() as root:
            del self.__dict__[key]
            del self.parent(root)[key]

    def __iter__(self):
        self.reload_cache()
        return iter(self.__dict__)

    def __len__(self):
        self.reload_cache()
        return len(self.__dict__)

    def __repr__(self):
        self.reload_cache()
        return '<%s[%s]=%s>' % (
            self.root.name,
            '.'.join(map(str, self.tree)),
            self.__dict__,
        )

    def setdefault(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            self[key] = default
        return self[key]


class DeepSerializer(JSONSerializer):

    __slots__ = ('smd',)

    encoder = JsonEncoder
    decoder = JsonDecoder

    def __init__(self, smd):
        self.smd = smd

    def loads(self, data):
        tree = ()
        db = super(DeepSerializer, self).loads(data)
        db = {
            key: self._unmap_value(tuple(list(tree) + [key]), val)
            for key, val in db.items()
        }
        return db

    def _unmap_value(self, tree, value):
        if isinstance(value, dict):
            db = {
                key: self._unmap_value(tuple(list(tree) + [key]), val)
                for key, val in value.items()
            }
            value = DictProxy.from_shared_memory_dict(self.smd, tree, db)
        return value


class NestedSharedMemoryDict(SharedMemoryDict):
    def __init__(
        self,
        name,
        size,
    ):
        super().__init__(name, size, serializer=json_serializer)
        self.name = name
        self._serializer = DeepSerializer(self)
