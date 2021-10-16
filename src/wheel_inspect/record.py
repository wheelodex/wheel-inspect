# Format defined in PEP 376
from __future__ import annotations
import base64
import csv
import hashlib
import re
import sys
from typing import Dict, Iterator, List, Optional, TextIO, Tuple
import attr
from . import errors
from .consts import PathType
from .mapping import AttrMapping
from .path import Path
from .util import find_special_dir, is_record_file

if sys.version_info[:2] >= (3, 8):
    from functools import cached_property
else:
    from cached_property import cached_property


@attr.define
class FileData:
    algorithm: str
    digest: str  # In the pseudo-base64 format
    size: int

    @property
    def b64_digest(self) -> str:
        # Alias for readability
        return self.digest

    @property
    def hex_digest(self) -> str:
        return self.bytes_digest.hex()

    @property
    def bytes_digest(self) -> bytes:
        return urlsafe_b64decode_nopad(self.digest)


@attr.define
class RecordPath(Path):
    # This is all smushed into one class instead of having separate FilePath
    # and DirectoryPath classes because the types of the Path methods that
    # return new Paths require the return values to be of the same class as the
    # invocant.
    filedata: Optional[FileData] = None
    _parent: Optional[RecordPath] = attr.field(default=None)
    _children: Optional[Dict[str, RecordPath]] = attr.field(default=None)
    _exists: bool = attr.field(default=True)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({str(self)!r}, filedata={self.filedata!r})"

    @classmethod
    def _mkroot(cls) -> RecordPath:
        return cls(parts=(), children={}, exists=True)

    def _mkchild(
        self,
        name: str,
        filedata: Optional[FileData] = None,
        children: Optional[Dict[str, RecordPath]] = None,
        exists: bool = True,
    ) -> RecordPath:
        if self.is_file():
            raise ValueError("Cannot create a child of a file")
        node = RecordPath(
            parts=self.parts + (name,),
            filedata=filedata,
            # attrs strips leading underscores in __init__ args
            parent=self,
            children=children,
            exists=exists,
        )
        if self._children is not None:
            if name in self._children:
                raise ValueError(
                    f"Path {str(self)!r} already has an entry named {name!r}"
                )
            self._children[name] = node
        return node

    def _attach(self, node: RecordPath) -> None:
        if self._children is None:
            raise ValueError("Cannot attach a path to a non-directory")
        node._parent = self
        self._children[node.name] = node

    def _mkdir(self, name: str) -> RecordPath:
        if self._children is None:
            raise ValueError("Cannot create a directory in a non-directory")
        try:
            n = self._children[name]
        except KeyError:
            return self._mkchild(name, children={}, exists=True)
        else:
            if n.is_dir():
                return n
            else:
                raise errors.RecordConflictError(str(n))

    @property
    def parent(self) -> RecordPath:
        return self._parent if self._parent is not None else self

    def get_subpath(self, name: str) -> RecordPath:
        if not name or "/" in name:
            raise ValueError("Invalid filename: {name!r}")
        if not self._exists:
            return self._mkchild(name, exists=False)
        elif self._children is not None:
            try:
                return self._children[name]
            except KeyError:
                return self._mkchild(name, exists=False)
        else:
            # self is a file
            raise errors.NotDirectoryError(str(self))

    def exists(self) -> bool:
        return self._exists

    def is_file(self) -> bool:
        return self._exists and self._children is None

    def is_dir(self) -> bool:
        return self._exists and self._children is not None

    @property
    def path_type(self) -> PathType:
        if not self.exists():
            ### TODO: Replace this with a different exception:
            raise errors.NoSuchPathError(str(self))
        elif self.is_file():
            return PathType.FILE
        else:
            return PathType.DIRECTORY

    def iterdir(self) -> Iterator[RecordPath]:
        if not self._exists:
            ### TODO: Replace this with a different exception:
            raise errors.NoSuchPathError(str(self))
        elif self._children is not None:
            return iter(self._children.values())
        else:
            # self is a file
            raise errors.NotDirectoryError(str(self))


@attr.define
class Record(AttrMapping[str, Optional[FileData]]):
    filetree: RecordPath = attr.Factory(RecordPath._mkroot)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.data!r})"

    @classmethod
    def load(cls, fp: TextIO) -> Record:
        r = cls()
        for fields in csv.reader(fp, delimiter=",", quotechar='"'):
            if not fields:
                continue
            path, data = cls.parse_row(fields)
            if not path.endswith("/"):
                if data is None and not is_record_file(path):
                    raise errors.NullEntryError(path)
            r._insert(path, data)
        return r

    @staticmethod
    def parse_row(fields: List[str]) -> Tuple[str, Optional[FileData]]:
        try:
            path, alg_digest, size = fields
        except ValueError:
            raise errors.RecordEntryLengthError(
                fields[0] if fields else None,
                len(fields),
            )
        if not path:
            raise errors.EmptyPathError()
        elif "//" in path or "." in path.split("/") or ".." in path.split("/"):
            raise errors.NonNormalizedPathError(path)
        elif path.startswith("/"):
            raise errors.AbsolutePathError(path)
        algorithm: Optional[str]
        digest: Optional[str]
        if alg_digest:
            try:
                algorithm, digest = parse_digest(alg_digest, path)
            except ValueError:
                raise errors.RecordAlgDigestError(path, alg_digest)
        else:
            algorithm = None
            digest = None
        isize: Optional[int]
        if size:
            try:
                isize = int(size)
            except ValueError:
                raise errors.RecordSizeError(path, size)
            if isize < 0:
                raise errors.RecordSizeError(path, size)
        else:
            isize = None
        if digest is None and isize is not None:
            raise errors.EmptyDigestError(path)
        elif digest is not None and isize is None:
            raise errors.EmptySizeError(path)
        if digest is None:
            assert algorithm is None
            assert isize is None
            return (path, None)
        else:
            assert algorithm is not None
            assert isize is not None
            return (path, FileData(algorithm, digest, isize))

    def _insert(self, path: str, data: Optional[FileData]) -> None:
        children: Optional[Dict[str, RecordPath]]
        if path.endswith("/"):
            spath = path[:-1]
            children = {}
        else:
            spath = path
            children = None
        *parts, name = spath.split("/")
        tree = self.filetree
        for p in parts:
            tree = tree._mkdir(p)
        assert tree._children is not None
        try:
            n = tree._children[name]
        except KeyError:
            tree._mkchild(name, filedata=data, children=children, exists=True)
        else:
            if n.filedata != data:
                raise errors.RecordConflictError(path)
        self.data[path] = data

    @cached_property
    def dist_info_dirname(self) -> str:
        top_dirs = [str(p) for p in self.filetree.iterdir() if p.is_dir()]
        return find_special_dir(".dist-info", top_dirs, required=True).rstrip("/")

    @cached_property
    def data_dirname(self) -> Optional[str]:
        top_dirs = [str(p) for p in self.filetree.iterdir() if p.is_dir()]
        dirname = find_special_dir(".data", top_dirs, required=False)
        if dirname is not None:
            dirname = dirname.rstrip("/")
        return dirname

    def for_json(self) -> Dict[str, Optional[FileData]]:
        return dict(self)


def parse_digest(s: str, path: str) -> Tuple[str, str]:
    algorithm, digest = s.split("=", 1)
    algorithm = algorithm.lower()
    if algorithm not in hashlib.algorithms_guaranteed:
        raise errors.UnknownAlgorithmError(path, algorithm)
    elif algorithm in ("md5", "sha1"):
        raise errors.WeakAlgorithmError(path, algorithm)
    sz = (getattr(hashlib, algorithm)().digest_size * 8 + 5) // 6
    if not re.fullmatch(r"[-_0-9A-Za-z]{%d}" % (sz,), digest):
        raise errors.RecordDigestError(path, algorithm, digest)
    try:
        urlsafe_b64decode_nopad(digest)
    except ValueError:
        raise errors.RecordDigestError(path, algorithm, digest)
    return (algorithm, digest)


def urlsafe_b64encode_nopad(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("us-ascii")


def urlsafe_b64decode_nopad(data: str) -> bytes:
    pad = "=" * (4 - (len(data) & 3))
    return base64.urlsafe_b64decode(data + pad)
