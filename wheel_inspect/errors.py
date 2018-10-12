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
