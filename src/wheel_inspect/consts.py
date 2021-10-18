from enum import Enum
import os
import re
from typing import Union

AnyPath = Union[bytes, str, "os.PathLike[bytes]", "os.PathLike[str]"]

DIGEST_CHUNK_SIZE = 65535

PROJECT_VERSION_RGX = (
    r"(?P<project>[A-Za-z0-9](?:[A-Za-z0-9._]*[A-Za-z0-9])?)"
    r"-(?P<version>[A-Za-z0-9_.!+]+)"
)

DIST_INFO_DIR_RGX = re.compile(fr"{PROJECT_VERSION_RGX}\.dist-info")

DATA_DIR_RGX = re.compile(fr"{PROJECT_VERSION_RGX}\.data")

# <https://discuss.python.org/t/identifying-parsing-binary-extension-filenames/>
MODULE_EXT_RGX = re.compile(r"(?<=.)\.(?:py|pyd|so|[-A-Za-z0-9_]+\.(?:pyd|so))\Z")


class PathType(Enum):
    FILE = "file"
    DIRECTORY = "directory"
    OTHER = "other"  # for symlinks, devices, sockets, etc. in the backing


class Tree(Enum):
    ALL = "ALL"
    ROOT = "ROOT"  # alias for purelib or platlib, depending
    PURELIB = "purelib"
    PLATLIB = "platlib"
    DIST_INFO = "dist-info"
    DATA = "data"  # The whole .data directory
