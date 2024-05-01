import base64
from binascii import hexlify, unhexlify
from collections import OrderedDict
import csv
import hashlib
import re
import attr
from . import errors


@attr.s
class Record:
    files = attr.ib()

    def __iter__(self):
        return iter(self.files.values())

    def __contains__(self, filename):
        return filename in self.files

    def for_json(self):
        return [e.for_json() for e in self.files.values()]


@attr.s
class RecordEntry:
    path = attr.ib()
    digest_algorithm = attr.ib()
    #: The digest in hex format
    digest = attr.ib()
    size = attr.ib()

    @classmethod
    def from_csv_fields(cls, fields):
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
        if size:
            try:
                size = int(size)
            except ValueError:
                raise errors.MalformedSizeError(path, size)
        else:
            size = None
        if digest is None and size is not None:
            raise errors.EmptyDigestError(path)
        elif digest is not None and size is None:
            raise errors.EmptySizeError(path)
        return cls(
            path=path,
            digest_algorithm=digest_algorithm,
            digest=digest,
            size=size,
        )

    def for_json(self):
        return {
            "path": self.path,
            "digests": (
                {self.digest_algorithm: hex2record_digest(self.digest)}
                if self.digest is not None
                else {}
            ),
            "size": self.size,
        }


def parse_record(fp):
    # Format defined in PEP 376
    files = OrderedDict()
    for fields in csv.reader(fp, delimiter=",", quotechar='"'):
        if not fields:
            continue
        entry = RecordEntry.from_csv_fields(fields)
        if entry.path in files and files[entry.path] != entry:
            raise errors.RecordConflictError(entry.path)
        files[entry.path] = entry
    return Record(files)


def hex2record_digest(data):
    return base64.urlsafe_b64encode(unhexlify(data)).decode("us-ascii").rstrip("=")


def record_digest2hex(data):
    pad = "=" * (4 - (len(data) & 3))
    return hexlify(base64.urlsafe_b64decode(data + pad)).decode("us-ascii")
