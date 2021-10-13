from __future__ import annotations
import base64
import csv
import hashlib
import re
from typing import Any, BinaryIO, Dict, Iterator, List, Optional, TextIO
import attr
from . import errors
from .util import digest_file


@attr.s(auto_attribs=True)
class Record:
    entries: Dict[str, RecordEntry] = attr.ib(factory=dict)

    @classmethod
    def load(cls, fp: TextIO) -> Record:
        # Format defined in PEP 376
        entries: Dict[str, RecordEntry] = {}
        for fields in csv.reader(fp, delimiter=",", quotechar='"'):
            if not fields:
                continue
            entry = RecordEntry.from_csv_fields(fields)
            if entry.path in entries and entries[entry.path] != entry:
                raise errors.RecordConflictError(entry.path)
            entries[entry.path] = entry
        return cls(entries)

    def dump(self, fp: TextIO) -> None:
        out = csv.writer(fp, delimiter=",", quotechar='"')
        for entry in self:
            out.writerow(entry.to_csv_fields())

    def __iter__(self) -> Iterator[RecordEntry]:
        return iter(self.entries.values())

    def __contains__(self, filename: str) -> bool:
        return filename in self.entries

    def __getitem__(self, filename: str) -> RecordEntry:
        return self.entries[filename]

    def for_json(self) -> List[dict]:
        return [e.for_json() for e in self]


@attr.s(auto_attribs=True)
class RecordEntry:
    path: str
    digest: Optional[Digest]
    size: Optional[int]

    @classmethod
    def from_csv_fields(cls, fields: List[str]) -> RecordEntry:
        try:
            path, alg_digest, size = fields
        except ValueError:
            raise errors.RecordLengthError(
                fields[0] if fields else None,
                len(fields),
            )
        if not path:
            raise errors.EmptyPathError()
        elif "//" in path or "." in path.split("/") or ".." in path.split("/"):
            raise errors.NonNormalizedPathError(path)
        elif path.startswith("/"):
            raise errors.AbsolutePathError(path)
        digest: Optional[Digest]
        if alg_digest:
            digest = Digest.parse(alg_digest, path)
        else:
            digest = None
        isize: Optional[int]
        if size:
            try:
                isize = int(size)
            except ValueError:
                raise errors.MalformedSizeError(path, size)
            if isize < 0:
                raise errors.MalformedSizeError(path, size)
        else:
            isize = None
        if digest is None and isize is not None:
            raise errors.EmptyDigestError(path)
        elif digest is not None and isize is None:
            raise errors.EmptySizeError(path)
        return cls(path=path, digest=digest, size=isize)

    def to_csv_fields(self) -> List[str]:
        return [
            self.path,
            str(self.digest) if self.digest is not None else "",
            str(self.size) if self.size is not None else "",
        ]

    def for_json(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "digest": self.digest.for_json() if self.digest is not None else None,
            "size": self.size,
        }


@attr.s(auto_attribs=True)
class Digest:
    algorithm: str
    digest: bytes

    @classmethod
    def parse(cls, s: str, path: str) -> Digest:
        ### TODO: Set the exceptions' `path`s to None when raising and have
        ### them filled in by the caller
        ### TODO: Raise a custom exception if the below line fails:
        algorithm, digest = s.split("=", 1)
        if algorithm not in hashlib.algorithms_guaranteed:
            raise errors.UnknownDigestError(path, algorithm)
        elif algorithm in ("md5", "sha1"):
            raise errors.WeakDigestError(path, algorithm)
        sz = (getattr(hashlib, algorithm)().digest_size * 8 + 5) // 6
        if not re.fullmatch(r"[-_0-9A-Za-z]{%d}" % (sz,), digest):
            raise errors.MalformedDigestError(path, algorithm, digest)
        ### TODO: Raise a custom exception if the digest decoding fails
        return cls(algorithm=algorithm, digest=urlsafe_b64decode_nopad(digest))

    def __str__(self) -> str:
        return f"{self.algorithm}={self.b64_digest}"

    @property
    def b64_digest(self) -> str:
        return urlsafe_b64encode_nopad(self.digest)

    @property
    def hex_digest(self) -> str:
        return self.digest.hex()

    def verify(self, fp: BinaryIO) -> None:
        digest = digest_file(fp, [self.algorithm])[self.algorithm]
        if self.hex_digest != digest:
            raise errors.RecordDigestMismatchError(
                ### TODO: Set `path` to None and then have caller fill in
                path="(unknown)",
                algorithm=self.algorithm,
                record_digest=self.hex_digest,
                actual_digest=digest,
            )

    def for_json(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "digest": self.b64_digest,
        }


def urlsafe_b64encode_nopad(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("us-ascii")


def urlsafe_b64decode_nopad(data: str) -> bytes:
    pad = "=" * (4 - (len(data) & 3))
    return base64.urlsafe_b64decode(data + pad)
