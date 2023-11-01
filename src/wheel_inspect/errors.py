from typing import Optional


class WheelValidationError(Exception):
    """Superclass for all wheel validation errors raised by this package"""

    pass


class RecordValidationError(WheelValidationError):
    """
    Superclass for all validation errors raised due to a wheel's :file:`RECORD`
    being inaccurate or incomplete
    """

    pass


class RecordSizeMismatchError(RecordValidationError):
    """
    Raised when the size of a file as declared in a wheel's :file:`RECORD` does
    not match the file's actual size
    """

    def __init__(self, path: str, record_size: int, actual_size: int) -> None:
        #: The path of the mismatched file
        self.path: str = path
        #: The size of the file as declared in the :file:`RECORD`
        self.record_size: int = record_size
        #: The file's actual size
        self.actual_size: int = actual_size

    def __str__(self) -> str:
        return (
            f"Size of file {self.path!r} listed as {self.record_size} in"
            f" RECORD, actually {self.actual_size}"
        )


class RecordDigestMismatchError(RecordValidationError):
    """
    Raised when a file's digest as declared in a wheel's :file:`RECORD` does
    not match the file's actual digest
    """

    def __init__(
        self, path: str, algorithm: str, record_digest: str, actual_digest: str
    ) -> None:
        #: The path of the mismatched file
        self.path: str = path
        #: The name of the digest algorithm
        self.algorithm: str = algorithm
        #: The file's digest as declared in the :file:`RECORD`, in hex
        self.record_digest: str = record_digest
        #: The file's actual digest, in hex
        self.actual_digest: str = actual_digest

    def __str__(self) -> str:
        return (
            f"{self.algorithm} digest of file {self.path!r} listed as"
            f" {self.record_digest} in RECORD, actually {self.actual_digest}"
        )


class FileMissingError(RecordValidationError):
    """
    Raised when a file listed in a wheel's :file:`RECORD` is not found in the
    wheel
    """

    def __init__(self, path: str) -> None:
        #: The path of the missing file
        self.path: str = path

    def __str__(self):
        return f"File declared in RECORD not found in archive: {self.path!r}"


class ExtraFileError(RecordValidationError):
    """
    Raised when a wheel contains a file that is not listed in the
    :file:`RECORD` (other than :file:`RECORD.jws` and :file:`RECORD.p7s`)
    """

    def __init__(self, path: str) -> None:
        #: The path of the extra file
        self.path: str = path

    def __str__(self):
        return f"File not declared in RECORD: {self.path!r}"


class MalformedRecordError(WheelValidationError):
    """
    Superclass for all validation errors raised due to a wheel's :file:`RECORD`
    being malformed
    """

    pass


class UnknownDigestError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` uses a digest not listed
    in `hashlib.algorithms_guaranteed`
    """

    def __init__(self, path: str, algorithm: str) -> None:
        #: The path the entry is for
        self.path: str = path
        #: The unknown digest algorithm
        self.algorithm: str = algorithm

    def __str__(self):
        return (
            f"RECORD entry for {self.path!r} uses an unknown digest algorithm:"
            f" {self.algorithm!r}"
        )


class WeakDigestError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` uses a digest weaker than
    sha256
    """

    def __init__(self, path: str, algorithm: str) -> None:
        #: The path the entry is for
        self.path: str = path
        #: The weak digest algorithm
        self.algorithm: str = algorithm

    def __str__(self) -> str:
        return (
            f"RECORD entry for {self.path!r} uses a weak digest algorithm:"
            f" {self.algorithm!r}"
        )


class MalformedDigestError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` contains a malformed or
    invalid digest
    """

    def __init__(self, path: str, algorithm: str, digest: str) -> None:
        #: The path the entry is for
        self.path: str = path
        #: The digest's declared algorithm
        self.algorithm: str = algorithm
        #: The malformed digest
        self.digest: str = digest

    def __str__(self) -> str:
        return (
            f"RECORD contains invalid {self.algorithm} base64 nopad digest for"
            f" {self.path!r}: {self.digest!r}"
        )


class MalformedSizeError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` contains a malformed or
    invalid file size
    """

    def __init__(self, path: str, size: str) -> None:
        #: The path the entry is for
        self.path: str = path
        #: The size (as a string)
        self.size: str = size

    def __str__(self) -> str:
        return f"RECORD contains invalid size for {self.path!r}: {self.size!r}"


class RecordConflictError(MalformedRecordError):
    """
    Raised when a wheel's :file:`RECORD` contains two or more conflicting
    entries for the same path
    """

    def __init__(self, path: str) -> None:
        #: The path with conflicting entries
        self.path: str = path

    def __str__(self) -> str:
        return f"RECORD contains multiple conflicting entries for {self.path!r}"


class EmptyDigestError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` has a size but not a
    digest
    """

    def __init__(self, path: str) -> None:
        #: The path the entry is for
        self.path: str = path

    def __str__(self) -> str:
        return f"RECORD entry for {self.path!r} has a size but no digest"


class EmptySizeError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` has a digest but not a
    size
    """

    def __init__(self, path: str) -> None:
        #: The path the entry is for
        self.path: str = path

    def __str__(self) -> str:
        return f"RECORD entry for {self.path!r} has a digest but no size"


class EmptyPathError(MalformedRecordError):
    """Raised when an entry in a wheel's :file:`RECORD` has an empty path"""

    def __str__(self) -> str:
        return "RECORD entry has an empty path"


class RecordLengthError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` has the wrong number of
    fields
    """

    def __init__(self, path: Optional[str], length: int) -> None:
        #: The path the entry is for (if nonempty)
        self.path: Optional[str] = path
        #: The number of fields in the entry
        self.length: int = length

    def __str__(self) -> str:
        if self.path is None:
            return "Empty RECORD entry (blank line)"
        else:
            return (
                f"RECORD entry for {self.path!r} has {self.length} fields;"
                " expected 3"
            )


class NullEntryError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` lacks both digest and size
    and the entry is not for the :file:`RECORD` itself
    """

    def __init__(self, path: str) -> None:
        #: The path the entry is for
        self.path: str = path

    def __str__(self) -> str:
        return f"RECORD entry for {self.path!r} lacks both digest and size"


class NonNormalizedPathError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` has a non-normalized path
    """

    def __init__(self, path: str) -> None:
        #: The non-normalized path
        self.path: str = path

    def __str__(self) -> str:
        return f"RECORD entry has a non-normalized path: {self.path!r}"


class AbsolutePathError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` has an absolute path
    """

    def __init__(self, path: str) -> None:
        #: The absolute path
        self.path: str = path

    def __str__(self) -> str:
        return f"RECORD entry has an absolute path: {self.path!r}"


class DistInfoError(WheelValidationError):
    """
    Raised when a wheel's :file:`*.dist-info` directory cannot be found or
    determined
    """

    pass


class MissingDistInfoFileError(WheelValidationError):
    """
    Raised when a given file is not found in the wheel's :file:`*.dist-info`
    directory
    """

    def __init__(self, path: str) -> None:
        #: The path to the file, relative to the :file:`*.dist-info` directory
        self.path: str = path

    def __str__(self) -> str:
        return f"File not found in *.dist-info directory: {self.path!r}"


class MissingMetadataError(MissingDistInfoFileError):
    """Raised when a wheel does not contain a :file:`METADATA` file"""

    def __init__(self):
        super().__init__("METADATA")


class MissingRecordError(MissingDistInfoFileError):
    """Raised when a wheel does not contain a :file:`RECORD` file"""

    def __init__(self):
        super().__init__("RECORD")


class MissingWheelInfoError(MissingDistInfoFileError):
    """Raised when a wheel does not contain a :file:`WHEEL` file"""

    def __init__(self):
        super().__init__("WHEEL")
