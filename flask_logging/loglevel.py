import logging
import threading
from typing import Any
from typing import Iterator
from typing import List
from typing import MutableMapping
from typing import Tuple
from typing import TypeVar
from typing import Union

LogLevel = Union[str, int]
V = TypeVar("V")

__all__ = ["LogLevelDict"]


class LogLevelDict(MutableMapping[LogLevel, V]):
    """
    A dictionary for looking up logging properties based on log level

    Looking up an intermediate level will return the record for the next
    highest level. If the dictionary only contains values for INFO (20)
    and CRITICAL (50), looking up WARNING will return the value for
    CRITICAL, and looking up DEBUG or INFO will return the value for INFO.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self._lock = threading.Lock()
        self._items: List[Tuple[int, V]] = sorted((self._corece_key(k), v) for k, v in dict(*args, **kwargs).items())

    def _corece_key(self, key: LogLevel) -> int:
        if isinstance(key, str):
            key = getattr(logging, key.upper())
        return int(key)

    def __getitem__(self, key: LogLevel) -> V:
        key = self._corece_key(key)
        with self._lock:
            for lvl, value in self._items:
                if lvl >= key:
                    return value
        raise KeyError(key)

    def __setitem__(self, key: LogLevel, value: V) -> None:
        key = self._corece_key(key)

        replace = False
        with self._lock:
            idx = 0
            for idx, (lvl, _) in enumerate(self._items):
                if lvl == key:
                    replace = True
                    break
                elif lvl > key:
                    break
            if replace:
                del self._items[idx]
            self._items.insert(idx, (key, value))

    def __delitem__(self, key: LogLevel) -> None:
        key = self._corece_key(key)

        with self._lock:
            idx = 0
            for idx, (lvl, _) in enumerate(self._items):
                if lvl == key:
                    break
            else:
                raise KeyError(key)
            del self._items[idx]

    def __iter__(self) -> Iterator[int]:
        for lvl, _ in self._items:
            yield lvl

    def __len__(self) -> int:
        return len(self._items)

    def __repr__(self) -> str:
        return "LogLevelDict({!r})".format(dict(self._items))
