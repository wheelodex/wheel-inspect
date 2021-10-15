from __future__ import annotations
import base64
import csv
import hashlib
import re
from typing import IO, Dict, List, Optional, TextIO, Tuple
import attr
from . import errors
from .util import digest_file, is_dist_info_path


@attr.define
class FileData:
    algorithm: str
    digest: str  # In the pseudo-base64 format
    size: int

    @classmethod
    def from_csv_fields(cls, fields: List[str]) -> Tuple[str, Optional[FileData]]:
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
            algorithm, digest = parse_digest(alg_digest, path)
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
            return (path, cls(algorithm, digest, isize))

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

    def for_json(self) -> dict:
        return attr.asdict(self)


def parse_digest(s: str, path: str) -> Tuple[str, str]:
    ### TODO: Raise a custom exception if the below line fails:
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


RecordType = Dict[str, Optional[FileData]]


def load_record(fp: TextIO) -> RecordType:
    # Format defined in PEP 376
    entries: RecordType = {}
    for fields in csv.reader(fp, delimiter=",", quotechar='"'):
        if not fields:
            continue
        path, data = FileData.from_csv_fields(fields)
        if data is None and not (
            path.endswith("/") or is_dist_info_path(path, "RECORD")
        ):
            raise errors.NullEntryError(path)
        if path in entries and entries[path] != data:
            raise errors.RecordConflictError(path)
        entries[path] = data
    return entries


def urlsafe_b64encode_nopad(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("us-ascii")


def urlsafe_b64decode_nopad(data: str) -> bytes:
    pad = "=" * (4 - (len(data) & 3))
    return base64.urlsafe_b64decode(data + pad)
