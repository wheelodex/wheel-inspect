class WheelValidationError(Exception):
    """ Superclass for all wheel validation errors raised by this package """
    pass


class InvalidFilenameError(WheelValidationError, ValueError):
    """ Raised when an invalid wheel filename is encountered """

    def __init__(self, filename):
        #: The invalid filename
        self.filename = filename

    def __str__(self):
        return 'Invalid wheel filename: ' + repr(self.filename)


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

    def __init__(self, path, record_size, actual_size):
        #: The path of the mismatched file
        self.path = path
        #: The size of the file as declared in the :file:`RECORD`
        self.record_size = record_size
        #: The file's actual size
        self.actual_size = actual_size

    def __str__(self):
        return 'Size of file {0.path!r} listed as {0.record_size} in RECORD,'\
               ' actually {0.actual_size}'.format(self)


class RecordDigestMismatchError(RecordValidationError):
    """
    Raised when a file's digest as declared in a wheel's :file:`RECORD` does
    not match the file's actual digest
    """

    def __init__(self, path, algorithm, record_digest, actual_digest):
        #: The path of the mismatched file
        self.path = path
        #: The name of the digest algorithm
        self.algorithm = algorithm
        #: The file's digest as declared in the :file:`RECORD`, in hex
        self.record_digest = record_digest
        #: The file's actual digest, in hex
        self.actual_digest = actual_digest

    def __str__(self):
        return '{0.algorithm} digest of file {0.path!r} listed as'\
               ' {0.record_digest} in RECORD, actually {0.actual_digest}'\
               .format(self)


class FileMissingError(RecordValidationError):
    """
    Raised when a file listed in a wheel's :file:`RECORD` is not found in the
    wheel
    """

    def __init__(self, path):
        #: The path of the missing file
        self.path = path

    def __str__(self):
        return 'File declared in RECORD not found in archive: '+repr(self.path)


class ExtraFileError(RecordValidationError):
    """
    Raised when a wheel contains a file that is not listed in the
    :file:`RECORD` (other than :file:`RECORD.jws` and :file:`RECORD.p7s`)
    """

    def __init__(self, path):
        #: The path of the extra file
        self.path = path

    def __str__(self):
        return 'File not declared in RECORD: {0.path!r}'.format(self)


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

    def __init__(self, path, algorithm):
        #: The path the entry is for
        self.path = path
        #: The unknown digest algorithm
        self.algorithm = algorithm

    def __str__(self):
        return 'RECORD entry for {0.path!r} uses an unknown digest algorithm:'\
               ' {0.algorithm!r}'.format(self)


class WeakDigestError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` uses a digest weaker than
    sha256
    """

    def __init__(self, path, algorithm):
        #: The path the entry is for
        self.path = path
        #: The weak digest algorithm
        self.algorithm = algorithm

    def __str__(self):
        return 'RECORD entry for {0.path!r} uses a weak digest algorithm:'\
               ' {0.algorithm!r}'.format(self)


class MalformedDigestError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` contains a malformed or
    invalid digest
    """

    def __init__(self, path, algorithm, digest):
        #: The path the entry is for
        self.path = path
        #: The digest's declared algorithm
        self.algorithm = algorithm
        #: The malformed digest
        self.digest = digest

    def __str__(self):
        return 'RECORD contains invalid {0.algorithm} base64 nopad digest for'\
               ' {0.path!r}: {0.digest!r}'.format(self)


class MalformedSizeError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` contains a malformed or
    invalid file size
    """

    def __init__(self, path, size):
        #: The path the entry is for
        self.path = path
        #: The size (as a string)
        self.size = size

    def __str__(self):
        return 'RECORD contains invalid size for {0.path!r}: {0.size!r}'\
               .format(self)


class RecordConflictError(MalformedRecordError):
    """
    Raised when a wheel's :file:`RECORD` contains two or more conflicting
    entries for the same path
    """

    def __init__(self, path):
        #: The path with conflicting entries
        self.path = path

    def __str__(self):
        return 'RECORD contains multiple conflicting entries for {0.path!r}'\
               .format(self)


class EmptyDigestError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` has a size but not a
    digest
    """

    def __init__(self, path):
        #: The path the entry is for
        self.path = path

    def __str__(self):
        return 'RECORD entry for {0.path!r} has a size but no digest'\
               .format(self)


class EmptySizeError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` has a digest but not a
    size
    """

    def __init__(self, path):
        #: The path the entry is for
        self.path = path

    def __str__(self):
        return 'RECORD entry for {0.path!r} has a digest but no size'\
               .format(self)


class EmptyPathError(MalformedRecordError):
    """ Raised when an entry in a wheel's :file:`RECORD` has an empty path """

    def __str__(self):
        return 'RECORD entry has an empty path'


class RecordLengthError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` has the wrong number of
    fields
    """

    def __init__(self, path, length):
        #: The path the entry is for (if nonempty)
        self.path = path
        #: The number of fields in the entry
        self.length = length

    def __str__(self):
        if self.path is None:
            return 'Empty RECORD entry (blank line)'
        else:
            return 'RECORD entry for {0.path!r} has {0.length} fields;'\
                   ' expected 3'.format(self)


class NullEntryError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` lacks both digest and size
    and the entry is not for the :file:`RECORD` itself
    """

    def __init__(self, path):
        #: The path the entry is for
        self.path = path

    def __str__(self):
        return 'RECORD entry for {0.path!r} lacks both digest and size'\
               .format(self)


class NonNormalizedPathError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` has a non-normalized path
    """

    def __init__(self, path):
        #: The non-normalized path
        self.path = path

    def __str__(self):
        return 'RECORD entry has a non-normalized path: {0.path!r}'.format(self)


class AbsolutePathError(MalformedRecordError):
    """
    Raised when an entry in a wheel's :file:`RECORD` has an absolute path
    """

    def __init__(self, path):
        #: The absolute path
        self.path = path

    def __str__(self):
        return 'RECORD entry has an absolute path: {0.path!r}'.format(self)


class MissingRecordError(WheelValidationError):
    """ Raised when a wheel does not contain a :file:`RECORD` file """

    def __str__(self):
        return 'No RECORD file in wheel'
