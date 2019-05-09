"""
Extract information from wheels

``wheel-inspect`` examines Python wheel files and outputs various information
about the contents within as JSON-serializable objects.  It can be invoked in
Python code as::

    from wheel_inspect import inspect_wheel

    output = inspect_wheel(path_to_wheel_file)

or from the command line with the ``wheel2json`` command.

Visit <https://github.com/jwodder/wheel-inspect> for more information.
"""

from .filename import ParsedWheelFilename, parse_wheel_filename
from .schema   import SCHEMA
from .wheelcls import Wheel, inspect_wheel

__version__      = '1.3.0'
__author__       = 'John Thorvald Wodder II'
__author_email__ = 'wheel-inspect@varonathe.org'
__license__      = 'MIT'
__url__          = 'https://github.com/jwodder/wheel-inspect'

__all__ = [
    'ParsedWheelFilename',
    'SCHEMA',
    'Wheel',
    'inspect_wheel',
    'parse_wheel_filename',
]
