from __future__ import annotations
import abc
import io
import os
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional
from zipfile import ZipFile
from wheel_filename import ParsedWheelFilename, parse_wheel_filename
from . import errors
from .metadata import parse_metadata
from .record import Record, parse_record
from .util import AnyPath, digest_file, find_dist_info_dir
from .wheel_info import parse_wheel_info


class DistInfoProvider(abc.ABC):
    """
    An interface for resources that are or contain a :file:`*.dist-info`
    directory
    """

    @abc.abstractmethod
    def basic_metadata(self) -> Dict[str, Any]:
        """
        Returns a `dict` of class-specific simple metadata about the resource
        """
        ...

    @abc.abstractmethod
    def open_dist_info_file(self, path: str) -> BinaryIO:
        """
        Returns a readable binary IO handle for reading the contents of the
        file at the given path beneath the :file:`*.dist-info` directory
        """
        ### TODO: Specify here that MissingDistInfoFileError is raised if file
        ### not found?
        ...

    @abc.abstractmethod
    def has_dist_info_file(self, path: str) -> bool:
        """
        Returns true iff a file exists at the given path beneath the
        :file:`*.dist-info` directory
        """
        ...

    def get_metadata(self) -> Dict[str, Any]:
        try:
            with self.open_dist_info_file("METADATA") as binfp, io.TextIOWrapper(
                binfp, "utf-8"
            ) as txtfp:
                return parse_metadata(txtfp)
        except errors.MissingDistInfoFileError:
            raise errors.MissingMetadataError()

    def get_record(self) -> Record:
        try:
            with self.open_dist_info_file("RECORD") as binfp, io.TextIOWrapper(
                binfp, "utf-8", newline=""
            ) as txtfp:
                # The csv module requires this file to be opened with
                # `newline=''`
                return parse_record(txtfp)
        except errors.MissingDistInfoFileError:
            raise errors.MissingRecordError()

    def get_wheel_info(self) -> Dict[str, Any]:
        try:
            with self.open_dist_info_file("WHEEL") as binfp, io.TextIOWrapper(
                binfp, "utf-8"
            ) as txtfp:
                return parse_wheel_info(txtfp)
        except errors.MissingDistInfoFileError:
            raise errors.MissingWheelInfoError()


class FileProvider(abc.ABC):
    @abc.abstractmethod
    def list_files(self) -> List[str]:
        """
        Returns a list of files in the resource.  Each file is represented as a
        relative ``/``-separated path as would appear in a :file:`RECORD` file.
        Directories are not included in the list.

        :rtype: List[str]
        """
        ...

    @abc.abstractmethod
    def has_directory(self, path: str) -> bool:
        """
        Returns true iff the directory at ``path`` exists in the resource.

        :param str path: a relative ``/``-separated path that ends with a ``/``
        :rtype: bool
        """
        ...

    @abc.abstractmethod
    def get_file_size(self, path: str) -> bool:
        """
        Returns the size of the file at ``path`` in bytes.

        :param str path: a relative ``/``-separated path
        :rtype: int
        """
        ...

    @abc.abstractmethod
    def get_file_hash(self, path: str, algorithm: str) -> str:
        """
        Returns a hexdigest of the contents of the file at ``path`` computed
        using the digest algorithm ``algorithm``.

        :param str path: a relative ``/``-separated path
        :param str algorithm: the name of the digest algorithm to use, as
            recognized by `hashlib`
        :rtype: str
        """
        ...


class DistInfoDir(DistInfoProvider):
    def __init__(self, path: AnyPath) -> None:
        self.path: Path = Path(os.fsdecode(path))

    def __enter__(self) -> DistInfoDir:
        return self

    def __exit__(self, *_exc: Any) -> bool:
        return False

    def basic_metadata(self) -> Dict[str, Any]:
        return {}

    def open_dist_info_file(self, path: str) -> BinaryIO:
        # returns a binary IO handle; raises MissingDistInfoFileError if file
        # does not exist
        try:
            return (self.path / path).open("rb")
        except FileNotFoundError:
            raise errors.MissingDistInfoFileError(path)

    def has_dist_info_file(self, path: str) -> bool:
        return (self.path / path).exists()


class WheelFile(DistInfoProvider, FileProvider):
    def __init__(self, path: AnyPath):
        self.path: Path = Path(os.fsdecode(path))
        self.parsed_filename: ParsedWheelFilename = parse_wheel_filename(self.path)
        self.fp: Optional[BinaryIO] = None
        self.zipfile: Optional[ZipFile] = None
        self._dist_info: Optional[str] = None

    def __enter__(self):
        self.fp = self.path.open("rb")
        self.zipfile = ZipFile(self.fp)
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        assert self.zipfile is not None
        assert self.fp is not None
        self.zipfile.close()
        self.fp.close()
        self.fp = None
        self.zipfile = None
        return False

    @property
    def dist_info(self) -> str:
        if self._dist_info is None:
            if self.zipfile is None:
                raise RuntimeError(
                    "WheelFile.dist_info cannot be determined when WheelFile"
                    " is not open in context"
                )
            self._dist_info = find_dist_info_dir(
                self.zipfile.namelist(),
                self.parsed_filename.project,
                self.parsed_filename.version,
            )
        return self._dist_info

    def basic_metadata(self) -> Dict[str, Any]:
        namebits = self.parsed_filename
        about = {
            "filename": self.path.name,
            "project": namebits.project,
            "version": namebits.version,
            "buildver": namebits.build,
            "pyver": namebits.python_tags,
            "abi": namebits.abi_tags,
            "arch": namebits.platform_tags,
            "file": {
                "size": self.path.stat().st_size,
            },
        }
        self.fp.seek(0)
        about["file"]["digests"] = digest_file(self.fp, ["md5", "sha256"])
        return about

    def open_dist_info_file(self, path: str) -> BinaryIO:
        # returns a binary IO handle; raises MissingDistInfoFileError if file
        # does not exist
        try:
            zi = self.zipfile.getinfo(self.dist_info + "/" + path)
        except KeyError:
            raise errors.MissingDistInfoFileError(path)
        else:
            return self.zipfile.open(zi)

    def has_dist_info_file(self, path: str) -> bool:
        try:
            self.zipfile.getinfo(self.dist_info + "/" + path)
        except KeyError:
            return False
        else:
            return True

    def list_files(self) -> List[str]:
        return [name for name in self.zipfile.namelist() if not name.endswith("/")]

    def has_directory(self, path: str) -> bool:
        if not path.endswith("/"):
            path += "/"
        if path == "/":
            return True
        return any(name.startswith(path) for name in self.zipfile.namelist())

    def get_file_size(self, path: str) -> int:
        return self.zipfile.getinfo(path).file_size

    def get_file_hash(self, path: str, algorithm: str) -> str:
        with self.zipfile.open(path) as fp:
            return digest_file(fp, [algorithm])[algorithm]
