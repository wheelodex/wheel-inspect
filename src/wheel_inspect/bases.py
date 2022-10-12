from __future__ import annotations
import abc
from collections.abc import Iterator
from fnmatch import fnmatchcase
from typing import Mapping, TypeVar
import attr
from .consts import PathType

K = TypeVar("K")
V = TypeVar("V")
V_co = TypeVar("V_co", covariant=True)

P = TypeVar("P", bound="Path")


@attr.define
class AttrMapping(Mapping[K, V_co]):
    data: dict[K, V_co] = attr.field(factory=dict, kw_only=True)

    def __getitem__(self, key: K) -> V_co:
        return self.data[key]

    def __iter__(self) -> Iterator[K]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)


"""
# In case it's needed later.
@attr.define
class AttrMutableMapping(AttrMapping, MutableMapping[K, V_co]):
    def __setitem__(self, key: K, value: V) -> None:
        self.data[key] = value

    def __delitem__(self, key: K) -> None:
        del self.data[key]

    def clear(self) -> None:
        self.data.clear()
"""


@attr.define
class Path(abc.ABC):
    parts: tuple[str, ...]

    def __str__(self) -> str:
        return "/".join(self.parts)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({str(self)!r})"

    @property
    def name(self) -> str:
        if self.is_root():
            return ""
        else:
            assert self.parts
            return self.parts[-1]

    @abc.abstractmethod
    def get_subpath(self: P, name: str) -> P:
        ...

    def __truediv__(self: P, path: str) -> P:
        p = self
        for q in self.split_path(path):
            p = p.get_subpath(q)
        return p

    def joinpath(self: P, *paths: str) -> P:
        p = self
        for q in paths:
            p /= q
        return p

    @staticmethod
    def split_path(path: str) -> tuple[str, ...]:
        if path.startswith("/"):
            raise ValueError(f"Absolute paths not allowed: {path!r}")
        return tuple(q for q in path.split("/") if q)

    def is_root(self) -> bool:
        return self.parts == ()

    @property
    def root_path(self: P) -> P:
        p = self
        while not p.is_root():
            p = p.parent
        return p

    @property
    @abc.abstractmethod
    def parent(self: P) -> P:
        # The parent of the root of a filetree is itself
        ...

    @property
    def parents(self: P) -> tuple[P, ...]:
        ps: list[P] = []
        p = self
        while not p.is_root():
            q = p.parent
            ps.append(q)
            p = q
        return tuple(ps)

    def with_name(self: P, name: str) -> P:
        return self.parent / name

    @property
    def suffix(self) -> str:
        i = self.name.rfind(".")
        if 0 < i < len(self.name) - 1:
            return self.name[i:]
        else:
            return ""

    @property
    def suffixes(self) -> list[str]:
        if self.name.endswith("."):
            return []
        name = self.name.lstrip(".")
        return ["." + suffix for suffix in name.split(".")[1:]]

    @property
    def stem(self) -> str:
        i = self.name.rfind(".")
        if 0 < i < len(self.name) - 1:
            return self.name[:i]
        else:
            return self.name

    def with_stem(self: P, stem: str) -> P:
        return self.with_name(stem + self.suffix)

    def with_suffix(self: P, suffix: str) -> P:
        if "/" in suffix or (suffix and not suffix.startswith(".")) or suffix == ".":
            raise ValueError(f"Invalid suffix: {suffix!r}")
        if not self.name:
            raise ValueError("Path has an empty name")
        if not self.suffix:
            name = self.name + suffix
        else:
            name = self.name[: -len(self.suffix)] + suffix
        return self.with_name(name)

    def match(self, pattern: str) -> bool:
        patparts = self.split_path(pattern)
        if not patparts:
            raise ValueError("Empty pattern")
        if len(patparts) > len(self.parts):
            return False
        for part, pat in zip(reversed(self.parts), reversed(patparts)):
            if not fnmatchcase(part, pat):
                return False
        return True

    @property
    @abc.abstractmethod
    def path_type(self) -> PathType:
        ...

    @abc.abstractmethod
    def exists(self) -> bool:
        ...

    @abc.abstractmethod
    def is_file(self) -> bool:
        ...

    @abc.abstractmethod
    def is_dir(self) -> bool:
        ...

    @abc.abstractmethod
    def iterdir(self: P) -> Iterator[P]:
        ...