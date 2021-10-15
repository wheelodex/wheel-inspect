"""
Extract information from wheels

``wheel-inspect`` examines Python wheel files and outputs various information
about the contents within as JSON-serializable objects.  It can be invoked in
Python code as::

    from wheel_inspect import inspect_wheel

    output = inspect_wheel(path_to_wheel_file)

or from the command line with the ``wheel2json`` command.

Visit <https://github.com/wheelodex/wheel-inspect> for more information.
"""

from .classes import (
    BackedDistInfo,
    DistInfoDir,
    DistInfoProvider,
    FileProvider,
    WheelFile,
)
from .inspecting import inspect_dist_info_dir, inspect_wheel
from .schema import DIST_INFO_SCHEMA, WHEEL_SCHEMA

__version__ = "2.0.0.dev1"
__author__ = "John Thorvald Wodder II"
__author_email__ = "wheel-inspect@varonathe.org"
__license__ = "MIT"
__url__ = "https://github.com/wheelodex/wheel-inspect"

__all__ = [
    "BackedDistInfo",
    "DIST_INFO_SCHEMA",
    "DistInfoDir",
    "DistInfoProvider",
    "FileProvider",
    "WHEEL_SCHEMA",
    "WheelFile",
    "inspect_dist_info_dir",
    "inspect_wheel",
]
