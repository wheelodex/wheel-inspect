from __future__ import annotations
import base64
from binascii import hexlify, unhexlify
import csv
import hashlib
import re
from typing import Any, Dict, Iterator, List, Optional, TextIO
import attr
from . import errors


@attr.s(auto_attribs=True)
class Record:
    files: Dict[str, RecordEntry] = attr.ib(factory=dict)

    def __iter__(self) -> Iterator[RecordEntry]:
        return iter(self.files.values())

    def __contains__(self, filename: str) -> bool:
        return filename in self.files

    def for_json(self) -> List[Dict[str, Any]]:
        return [e.for_json() for e in self.files.values()]


@attr.s(auto_attribs=True)
class RecordEntry:
    path: str
    digest_algorithm: Optional[str]
    #: The digest in hex format
    digest: Optional[str]
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
        digest_algorithm: Optional[str]
        digest: Optional[str]
        if alg_digest:
            digest_algorithm, digest = alg_digest.split("=", 1)
            if digest_algorithm not in hashlib.algorithms_guaranteed:
                raise errors.UnknownDigestError(path, digest_algorithm)
            elif digest_algorithm in ("md5", "sha1"):
                raise errors.WeakDigestError(path, digest_algorithm)
            sz = (getattr(hashlib, digest_algorithm)().digest_size * 8 + 5) // 6
            if not re.fullmatch(r"[-_0-9A-Za-z]{%d}" % (sz,), digest):
                raise errors.MalformedDigestError(path, digest_algorithm, digest)
            digest = record_digest2hex(digest)
        else:
            digest_algorithm, digest = None, None
        isize: Optional[int]
        if size:
            try:
                isize = int(size)
            except ValueError:
                raise errors.MalformedSizeError(path, size)
        else:
            isize = None
        if digest is None and isize is not None:
            raise errors.EmptyDigestError(path)
        elif digest is not None and isize is None:
            raise errors.EmptySizeError(path)
        return cls(
            path=path,
            digest_algorithm=digest_algorithm,
            digest=digest,
            size=isize,
        )

    def for_json(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "digests": {self.digest_algorithm: hex2record_digest(self.digest)}
            if self.digest is not None
            else {},
            "size": self.size,
        }


def parse_record(fp: TextIO) -> Record:
    # Format defined in PEP 376
    files: Dict[str, RecordEntry] = {}
    for fields in csv.reader(fp, delimiter=",", quotechar='"'):
        if not fields:
            continue
        entry = RecordEntry.from_csv_fields(fields)
        if entry.path in files and files[entry.path] != entry:
            raise errors.RecordConflictError(entry.path)
        files[entry.path] = entry
    return Record(files)


def hex2record_digest(data: str) -> str:
    return base64.urlsafe_b64encode(unhexlify(data)).decode("us-ascii").rstrip("=")


def record_digest2hex(data: str) -> str:
    pad = "=" * (4 - (len(data) & 3))
    return hexlify(base64.urlsafe_b64decode(data + pad)).decode("us-ascii")
