from typing import Optional
import attr


class Error(Exception):
    """Superclass for all errors raised by this package"""

    pass


class WheelValidationError(Error):
    """Superclass for all wheel validation errors raised by this package"""

    pass


class RecordValidationError(WheelValidationError):
    """
    Superclass for all validation errors raised due to a wheel's :file:`RECORD`
    being inaccurate or incomplete
    """

    pass


@attr.define
class RecordSizeMismatchError(RecordValidationError):
    """
    Raised when the size of a file as declared in a wheel's :file:`RECORD` does
    not match the file's actual size
    """

    #: The path of the mismatched file
    path: str
    #: The size of the file as declared in the :file:`RECORD`
    record_size: int
    #: The file's actual size
    actual_size: int

    def __str__(self) -> str:
        return (
            f"Size of file {self.path!r} listed as {self.record_size} in"
            f" RECORD, actually {self.actual_size}"
        )


@attr.define
class RecordDigestMismatchError(RecordValidationError):
    """
    Raised when a file's digest as declared in a wheel's :file:`RECORD` does
    not match the file's actual digest
    """

    #: The path of the mismatched file
    path: str
    #: The name of the digest algorithm
    algorithm: str
    #: The file's digest as declared in the :file:`RECORD`, in hex
    record_digest: str
    #: The file's actual digest, in hex
    actual_digest: str

    def __str__(self) -> str:
        return (
            f"{self.algorithm} digest of file {self.path!r} listed as"
            f" {self.record_digest} in RECORD, actually {self.actual_digest}"
        )


@attr.define
class FileMissingError(RecordValidationError):
    """
    Raised when a file listed in a wheel's :file:`RECORD` is not found in the
    wheel
    """

    #: The path of the missing file
    path: str

    def __str__(self) -> str:
        return f"File declared in RECORD not found in archive: {self.path!r}"


@attr.define
class ExtraFileError(RecordValidationError):
    """
    Raised when a wheel contains a file that is not listed in the
    :file:`RECORD` (other than :file:`RECORD.jws` and :file:`RECORD.p7s`)
    """

    #: The path of the extra file
    path: str

    def __str__(self) -> str:
        return f"File not declared in RECORD: {self.path!r}"


class MalformedRecordError(WheelValidationError):
    """
    Superclass for all validation errors raised due to a wheel's :file:`RECORD`
    being malformed
    """

    pass


@attr.define
class UnknownDigestError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` uses a digest not listed
    in `hashlib.algorithms_guaranteed`
    """

    #: The path the entry is for
    path: str
    #: The unknown digest algorithm
    algorithm: str

    def __str__(self) -> str:
        return (
            f"RECORD entry for {self.path!r} uses an unknown digest algorithm:"
            f" {self.algorithm!r}"
        )


@attr.define
class WeakDigestError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` uses a digest weaker than
    sha256
    """

    #: The path the entry is for
    path: str
    #: The weak digest algorithm
    algorithm: str

    def __str__(self) -> str:
        return (
            f"RECORD entry for {self.path!r} uses a weak digest algorithm:"
            f" {self.algorithm!r}"
        )


@attr.define
class MalformedDigestError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` contains a malformed or
    invalid digest
    """

    #: The path the entry is for
    path: str
    #: The digest's declared algorithm
    algorithm: str
    #: The malformed digest
    digest: str

    def __str__(self) -> str:
        return (
            f"RECORD contains invalid {self.algorithm} base64 nopad digest for"
            f" {self.path!r}: {self.digest!r}"
        )


@attr.define
class MalformedSizeError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` contains a malformed or
    invalid file size
    """

    #: The path the entry is for
    path: str
    #: The size (as a string)
    size: str

    def __str__(self) -> str:
        return f"RECORD contains invalid size for {self.path!r}: {self.size!r}"


@attr.define
class RecordConflictError(MalformedRecordError):
    """
    Raised when a wheel's :file:`RECORD` contains two or more conflicting
    entries for the same path
    """

    #: The path with conflicting entries
    path: str

    def __str__(self) -> str:
        return f"RECORD contains multiple conflicting entries for {self.path!r}"


@attr.define
class EmptyDigestError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` has a size but not a
    digest
    """

    #: The path the entry is for
    path: str

    def __str__(self) -> str:
        return f"RECORD entry for {self.path!r} has a size but no digest"


@attr.define
class EmptySizeError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` has a digest but not a
    size
    """

    #: The path the entry is for
    path: str

    def __str__(self) -> str:
        return f"RECORD entry for {self.path!r} has a digest but no size"


class EmptyPathError(MalformedRecordError):
    """Raised when an entry in a wheel's :file:`RECORD` has an empty path"""

    def __str__(self) -> str:
        return "RECORD entry has an empty path"


@attr.define
class RecordLengthError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` has the wrong number of
    fields
    """

    #: The path the entry is for (if nonempty)
    path: Optional[str]
    #: The number of fields in the entry
    length: int

    def __str__(self) -> str:
        if self.path is None:
            return "Empty RECORD entry (blank line)"
        else:
            return (
                f"RECORD entry for {self.path!r} has {self.length} fields;"
                " expected 3"
            )


@attr.define
class NullEntryError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` lacks both digest and size
    and the entry is not for the :file:`RECORD` itself
    """

    #: The path the entry is for
    path: str

    def __str__(self) -> str:
        return f"RECORD entry for {self.path!r} lacks both digest and size"


@attr.define
class NonNormalizedPathError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` has a non-normalized path
    """

    #: The non-normalized path
    path: str

    def __str__(self) -> str:
        return f"RECORD entry has a non-normalized path: {self.path!r}"


@attr.define
class AbsolutePathError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` has an absolute path
    """

    #: The absolute path
    path: str

    def __str__(self) -> str:
        return f"RECORD entry has an absolute path: {self.path!r}"


class DistInfoError(WheelValidationError):
    """
    Raised when a wheel's :file:`*.dist-info` directory cannot be found or
    determined
    """

    pass


@attr.define
class MissingDistInfoFileError(WheelValidationError):
    """
    Raised when a given file is not found in the wheel's :file:`*.dist-info`
    directory
    """

    #: The path to the file, relative to the :file:`*.dist-info` directory
    path: str

    def __str__(self) -> str:
        return f"File not found in *.dist-info directory: {self.path!r}"


@attr.define
class NoSuchFileError(Error):
    """Raised when a file requested by the user is not found in the wheel"""

    #: The path to the file
    path: str

    def __str__(self) -> str:
        return f"File not found in wheel: {self.path!r}"
