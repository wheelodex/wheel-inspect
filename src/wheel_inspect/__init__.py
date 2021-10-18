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
    BackedFiletreeMapping,
    BackedTreePath,
    DistInfoDir,
    DistInfoProvider,
    FileProvider,
    FiletreeMapping,
    TreePath,
    WheelFile,
)
from .consts import PathType, Tree
from .inspecting import inspect, inspect_dist_info_dir, inspect_wheel
from .path import Path
from .record import FileData, Record, RecordPath
from .schema import WHEEL_SCHEMA

__version__ = "2.0.0.dev1"
__author__ = "John Thorvald Wodder II"
__author_email__ = "wheel-inspect@varonathe.org"
__license__ = "MIT"
__url__ = "https://github.com/wheelodex/wheel-inspect"

__all__ = [
    "BackedDistInfo",
    "BackedFiletreeMapping",
    "BackedTreePath",
    "DistInfoDir",
    "DistInfoProvider",
    "FileData",
    "FileProvider",
    "FiletreeMapping",
    "Path",
    "PathType",
    "Record",
    "RecordPath",
    "Tree",
    "TreePath",
    "WHEEL_SCHEMA",
    "WheelFile",
    "inspect",
    "inspect_dist_info_dir",
    "inspect_wheel",
]
