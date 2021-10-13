from __future__ import annotations
import abc
import io
import os
from pathlib import Path
from typing import IO, Any, Dict, List, Optional, TextIO, TypeVar, overload
from zipfile import ZipFile
from wheel_filename import ParsedWheelFilename, parse_wheel_filename
from . import errors as exc
from .metadata import parse_metadata
from .record import Record
from .util import AnyPath, digest_file, find_dist_info_dir
from .wheel_info import parse_wheel_info

T = TypeVar("T", bound="DistInfoProvider")


class DistInfoProvider(abc.ABC):
    """
    An interface for resources that are or contain a :file:`*.dist-info`
    directory
    """

    def __enter__(self: T) -> T:
        return self

    def __exit__(self, *_exc: Any) -> Optional[bool]:
        pass

    @abc.abstractmethod
    def basic_metadata(self) -> Dict[str, Any]:
        """
        Returns a `dict` of class-specific simple metadata about the resource
        """
        ...

    @overload
    def open_dist_info_file(
        self,
        path: str,
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> IO[bytes]:
        ...

    @overload
    def open_dist_info_file(
        self,
        path: str,
        encoding: str,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> TextIO:
        ...

    @abc.abstractmethod
    def open_dist_info_file(
        self,
        path: str,
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO:
        """
        Returns a readable IO handle for reading the contents of the file at
        the given path beneath the :file:`*.dist-info` directory.  If
        ``encoding`` is `None`, the handle is a binary handle; otherwise, it is
        a text handle decoded using the given encoding.

        :raises MissingDistInfoFileError: if the given file does not exist
        """
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
            with self.open_dist_info_file("METADATA", encoding="utf-8") as fp:
                return parse_metadata(fp)
        except exc.MissingDistInfoFileError:
            raise exc.MissingMetadataError()

    def get_record(self) -> Record:
        try:
            with self.open_dist_info_file("RECORD", encoding="utf-8", newline="") as fp:
                # The csv module requires this file to be opened with
                # `newline=''`
                return Record.load(fp)
        except exc.MissingDistInfoFileError:
            raise exc.MissingRecordError()

    def get_wheel_info(self) -> Dict[str, Any]:
        try:
            with self.open_dist_info_file("WHEEL", encoding="utf-8") as fp:
                return parse_wheel_info(fp)
        except exc.MissingDistInfoFileError:
            raise exc.MissingWheelInfoError()


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
    def get_file_size(self, path: str) -> int:
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

    def basic_metadata(self) -> Dict[str, Any]:
        return {}

    @overload
    def open_dist_info_file(
        self,
        path: str,
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> IO[bytes]:
        ...

    @overload
    def open_dist_info_file(
        self,
        path: str,
        encoding: str,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> TextIO:
        ...

    def open_dist_info_file(
        self,
        path: str,
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO:
        try:
            if encoding is None:
                return (self.path / path).open("rb")
            else:
                return (self.path / path).open(
                    "r", encoding=encoding, errors=errors, newline=newline
                )
        except FileNotFoundError:
            raise exc.MissingDistInfoFileError(path)

    def has_dist_info_file(self, path: str) -> bool:
        return (self.path / path).exists()


class WheelFile(DistInfoProvider, FileProvider):
    def __init__(self, path: AnyPath):
        self.path: Path = Path(os.fsdecode(path))
        self.filename: ParsedWheelFilename = parse_wheel_filename(self.path)
        self.fp: IO[bytes] = self.path.open("rb")
        self.zipfile: ZipFile = ZipFile(self.fp)
        self._dist_info: Optional[str] = None

    @classmethod
    def from_zipfile_path(cls, path: AnyPath) -> WheelFile:
        # Recommend the use of this method in case __init__'s signature changes
        # later
        return cls(path)

    def __enter__(self) -> WheelFile:
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()

    def close(self) -> None:
        self.zipfile.close()
        self.fp.close()

    @property
    def closed(self) -> bool:
        return self.fp.closed

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
                self.filename.project,
                self.filename.version,
            )
        return self._dist_info

    def basic_metadata(self) -> Dict[str, Any]:
        namebits = self.filename
        about: Dict[str, Any] = {
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

    @overload
    def open_dist_info_file(
        self,
        path: str,
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> IO[bytes]:
        ...

    @overload
    def open_dist_info_file(
        self,
        path: str,
        encoding: str,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> TextIO:
        ...

    def open_dist_info_file(
        self,
        path: str,
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO:
        try:
            zi = self.zipfile.getinfo(self.dist_info + "/" + path)
        except KeyError:
            raise exc.MissingDistInfoFileError(path)
        fp = self.zipfile.open(zi)
        if encoding is not None:
            return io.TextIOWrapper(
                fp, encoding=encoding, errors=errors, newline=newline
            )
        else:
            return fp

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
