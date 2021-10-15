from typing import Dict, Iterator, Mapping, MutableMapping, TypeVar
import attr

K = TypeVar("K")
V = TypeVar("V")
V_co = TypeVar("V_co", covariant=True)


@attr.define
class AttrMapping(Mapping[K, V_co]):
    data: Dict[K, V_co] = attr.Factory(dict)

    def __getitem__(self, key: K) -> V_co:
        return self.data[key]

    def __iter__(self) -> Iterator[K]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)


@attr.define
class AttrMutableMapping(AttrMapping, MutableMapping[K, V_co]):
    def __setitem__(self, key: K, value: V) -> None:
        self.data[key] = value

    def __delitem__(self, key: K) -> None:
        del self.data[key]

    def clear(self) -> None:
        self.data.clear()
