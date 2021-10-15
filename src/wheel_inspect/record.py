# Format defined in PEP 376
from __future__ import annotations
import base64
import csv
import hashlib
import re
from typing import IO, Dict, List, Optional, TextIO, Tuple
import attr
from . import errors
from .mapping import AttrMapping
from .util import digest_file, is_dist_info_path


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

    def verify(self, fp: IO[bytes], path: str) -> None:
        digests, actual_size = digest_file(fp, [self.algorithm])
        actual_digest = digests[self.algorithm]
        if self.hex_digest != actual_digest:
            raise errors.DigestMismatchError(
                path=path,
                algorithm=self.algorithm,
                record_digest=self.hex_digest,
                actual_digest=actual_digest,
            )
        if self.size != actual_size:
            raise errors.SizeMismatchError(
                path=path,
                record_size=self.size,
                actual_size=actual_size,
            )


@attr.define(slots=False)
# Inheriting from multiple slotted classes doesn't work
class RecordNode:
    parts: Tuple[str, ...]
    filedata: Optional[FileData] = None

    @property
    def name(self) -> str:
        return (("",) + self.parts)[-1]

    @property
    def path(self) -> str:
        return "/".join(self.parts)


@attr.define
class FileNode(RecordNode):
    pass


@attr.define
class DirectoryNode(RecordNode, AttrMapping[str, RecordNode]):
    def _mkdir(self, name: str) -> DirectoryNode:
        try:
            n = self[name]
        except KeyError:
            d = DirectoryNode(parts=self.parts + (name,))
            self.data[name] = d
            return d
        else:
            if isinstance(n, DirectoryNode):
                return n
            else:
                raise errors.RecordConflictError(self.path)


@attr.define
class Record(AttrMapping[str, Optional[FileData]]):
    filetree: DirectoryNode = attr.Factory(lambda: DirectoryNode(parts=()))

    @classmethod
    def load(cls, fp: TextIO) -> Record:
        r = cls()
        for fields in csv.reader(fp, delimiter=",", quotechar='"'):
            if not fields:
                continue
            path, data = cls.parse_row(fields)
            if not path.endswith("/"):
                if data is None and not is_dist_info_path(path, "RECORD"):
                    raise errors.NullEntryError(path)
                r._insert_file(path, data)
            else:
                # TODO: Raise error if data is not None?
                r._insert_directory(path)
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

    def _insert_file(self, path: str, data: Optional[FileData]) -> None:
        self._insert_node(FileNode(parts=tuple(path.split("/")), filedata=data))
        self.data[path] = data

    def _insert_directory(self, path: str) -> None:
        self._insert_node(DirectoryNode(parts=tuple(path.split("/"))))
        self.data[path] = None

    def _insert_node(self, node: RecordNode) -> None:
        *parts, name = node.parts
        tree = self.filetree
        for p in parts:
            if isinstance(tree, DirectoryNode):
                tree = tree._mkdir(p)
            else:
                raise errors.RecordConflictError(tree.path)
        try:
            n = tree[name]
        except KeyError:
            tree.data[name] = node
        else:
            if n != node:
                raise errors.RecordConflictError(node.path)

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
