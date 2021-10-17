from typing import Optional
import attr
from .consts import PathType


class Error(Exception):
    """Superclass for all errors raised by this package"""

    pass


class WheelError(Error):
    """
    Superclass for all validation & verification errors raised by this package
    """

    pass


class ValidationError(WheelError):
    """Superclass for all validation errors raised by this package"""

    pass


@attr.define
class VerificationError(WheelError):
    """
    Superclass for all verification errors raised due to a :file:`RECORD` file
    not matching the backing files
    """

    #: The path that failed verification
    path: str


@attr.define
class PathTypeMismatchError(VerificationError):
    """
    Raised when the type of a path as declared in a :file:`RECORD` file does
    not match the type of the actual path
    """

    record_type: PathType
    actual_type: PathType

    def __str__(self) -> str:
        return (
            f"Type of path {self.path!r} listed as {self.record_type} in"
            f" RECORD, actually {self.actual_type}"
        )


@attr.define
class SizeMismatchError(VerificationError):
    """
    Raised when the size of a file as declared in a :file:`RECORD` file does
    not match the file's actual size
    """

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
class DigestMismatchError(VerificationError):
    """
    Raised when a file's digest as declared in a :file:`RECORD` file does not
    match the file's actual digest
    """

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
class MissingPathError(VerificationError):
    """
    Raised when a path listed in a :file:`RECORD` file is not found in the
    backing
    """

    def __str__(self) -> str:
        return f"Path declared in RECORD does not exist: {self.path!r}"


@attr.define
class UnrecordedPathError(VerificationError):
    """
    Raised when a backing contains a path that is not listed in the
    :file:`RECORD` (other than :file:`RECORD.jws` and :file:`RECORD.p7s`)
    """

    def __str__(self) -> str:
        return f"Path not declared in RECORD: {self.path!r}"


class RecordError(ValidationError):
    """
    Superclass for all validation errors raised due to a :file:`RECORD` file
    being malformed
    """

    pass


@attr.define
class RecordEntryError(RecordError):
    """
    Superclass for all validation errors raised due to an individual entry in a
    :file:`RECORD` file being malformed
    """

    #: The path the entry is for (if given)
    path: Optional[str]


@attr.define
class RecordEntryLengthError(RecordEntryError):
    """
    Raised when an entry in a :file:`RECORD` file has the wrong number of
    fields
    """

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
class NullEntryError(RecordEntryError):
    """
    Raised when an entry in a :file:`RECORD` file lacks both digest and size
    and the entry is not for a directory, a signature file, or the
    :file:`RECORD` itself
    """

    #: The path the entry is for
    path: str

    def __str__(self) -> str:
        return f"RECORD entry for {self.path!r} lacks both digest and size"


@attr.define
class RecordPathError(RecordEntryError):
    """
    Raised when an an entry in a :file:`RECORD` file has an invalid path
    """

    #: The path in question
    path: str


@attr.define
class EmptyPathError(RecordPathError):
    """Raised when an entry in a :file:`RECORD` file has an empty path"""

    path: str = ""

    def __str__(self) -> str:
        return "RECORD entry has an empty path"


@attr.define
class NonNormalizedPathError(RecordPathError):
    """
    Raised when an entry in a :file:`RECORD` file has a non-normalized path
    """

    def __str__(self) -> str:
        return f"RECORD entry has a non-normalized path: {self.path!r}"


@attr.define
class AbsolutePathError(RecordPathError):
    """Raised when an entry in a :file:`RECORD` file has an absolute path"""

    def __str__(self) -> str:
        return f"RECORD entry has an absolute path: {self.path!r}"


@attr.define
class RecordSizeError(RecordEntryError):
    """
    Raised when an entry in a :file:`RECORD` file contains a malformed or
    invalid file size
    """

    #: The path the entry is for
    path: str
    #: The size (as a string)
    size: str

    def __str__(self) -> str:
        return f"RECORD contains invalid size for {self.path!r}: {self.size!r}"


@attr.define
class EmptySizeError(RecordSizeError):
    """
    Raised when an entry in a :file:`RECORD` file has a digest but not a size
    """

    size: str = ""

    def __str__(self) -> str:
        return f"RECORD entry for {self.path!r} has a digest but no size"


@attr.define
class RecordAlgDigestError(RecordEntryError):
    """
    Raised when a record entry's algorithm+digest field is completely
    unparseable
    """

    #: The path the entry is for
    path: str
    #: The value of the field in question
    alg_digest: str

    def __str__(self) -> str:
        return (
            f"RECORD entry for {self.path!r} has an unparseable"
            f" algorithm+digest field: {self.alg_digest!r}"
        )


@attr.define
class RecordAlgorithmError(RecordEntryError):
    """
    Raised when an entry in a :file:`RECORD` file uses an invalid digest
    algorithm
    """

    #: The path the entry is for
    path: str
    #: The algorithm in question
    algorithm: str


@attr.define
class UnknownAlgorithmError(RecordAlgorithmError):
    """
    Raised when an entry in a :file:`RECORD` file uses a digest algorithm not
    listed in `hashlib.algorithms_guaranteed`
    """

    def __str__(self) -> str:
        return (
            f"RECORD entry for {self.path!r} uses an unknown digest algorithm:"
            f" {self.algorithm!r}"
        )


@attr.define
class WeakAlgorithmError(RecordAlgorithmError):
    """
    Raised when an entry in a :file:`RECORD` file uses a digest algorithm
    weaker than sha256
    """

    def __str__(self) -> str:
        return (
            f"RECORD entry for {self.path!r} uses a weak digest algorithm:"
            f" {self.algorithm!r}"
        )


@attr.define
class RecordDigestError(RecordEntryError):
    """
    Raised when an entry in a :file:`RECORD` file contains a malformed or
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
            f"RECORD entry for {self.path!r} contains invalid {self.algorithm}"
            f" base64 nopad digest: {self.digest!r}"
        )


@attr.define
class EmptyDigestError(RecordDigestError):
    """
    Raised when an entry in a :file:`RECORD` file has a size but not a digest
    """

    algorithm: str = ""
    digest: str = ""

    def __str__(self) -> str:
        return f"RECORD entry for {self.path!r} has a size but no digest"


@attr.define
class RecordConflictError(RecordError):
    """
    Raised when a :file:`RECORD` file contains two or more conflicting entries
    for the same path
    """

    #: The path with conflicting entries
    path: str

    def __str__(self) -> str:
        return f"RECORD contains multiple conflicting entries for {self.path!r}"


class SpecialDirError(ValidationError):
    """
    Raised when a wheel's :file:`*.dist-info` or :file:`*.data` directory
    cannot be found or determined
    """

    pass


@attr.define
class MissingDistInfoFileError(ValidationError):
    """
    Raised when a required file is absent from the :file:`*.dist-info`
    directory
    """

    #: The path to the missing file, relative to the :file:`*.dist-info`
    #: directory
    path: str

    def __str__(self) -> str:
        return f"Required file not present in *.dist-info directory: {self.path!r}"


@attr.define
class NoSuchPathError(Error):
    """
    Raised when a path requested by the user is not found in the wheel or
    backing
    """

    #: The requested path
    path: str

    def __str__(self) -> str:
        return f"Path does not exist: {self.path!r}"


@attr.define
class NotDirectoryError(Error):
    """Raised when a directory-specific operation is attempted on a file path"""

    #: The path to the file operated on
    path: str

    def __str__(self) -> str:
        return f"Not a directory: {self.path!r}"
