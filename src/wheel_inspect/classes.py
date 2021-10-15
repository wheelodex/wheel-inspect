from __future__ import annotations
import abc
import io
import os
from pathlib import Path
import sys
from typing import IO, Any, Dict, List, Optional, TextIO, TypeVar, overload
from zipfile import ZipFile
import attr
from entry_points_txt import EntryPointSet
from entry_points_txt import load as load_entry_points
from wheel_filename import ParsedWheelFilename, parse_wheel_filename
from . import errors as exc
from .metadata import parse_metadata
from .record import Record
from .util import AnyPath, digest_file, find_special_dir, is_dist_info_path, mkpath
from .wheel_info import parse_wheel_info

if sys.version_info[:2] >= (3, 8):
    from functools import cached_property
else:
    from cached_property import cached_property


T = TypeVar("T", bound="DistInfoProvider")


class DistInfoProvider(abc.ABC):
    """
    An abstract class for resources that are or contain a :file:`*.dist-info`
    directory
    """

    def __enter__(self: T) -> T:
        return self

    def __exit__(self, *_exc: Any) -> Optional[bool]:
        pass

    @overload
    def open_dist_info_file(
        self,
        path: str,
        encoding: None = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
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

    @cached_property
    def metadata(self) -> Dict[str, Any]:
        with self.open_dist_info_file("METADATA", encoding="utf-8") as fp:
            return parse_metadata(fp)

    @cached_property
    def record(self) -> Record:
        with self.open_dist_info_file("RECORD", encoding="utf-8", newline="") as fp:
            # The csv module requires this file to be opened with
            # `newline=''`
            return Record.load(fp)

    @cached_property
    def wheel_info(self) -> Dict[str, Any]:
        with self.open_dist_info_file("WHEEL", encoding="utf-8") as fp:
            return parse_wheel_info(fp)

    @cached_property
    def entry_points(self) -> EntryPointSet:
        try:
            with self.open_dist_info_file("entry_points.txt", encoding="utf-8") as fp:
                return load_entry_points(fp)
        except exc.MissingDistInfoFileError:
            return {}


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
    def has_file(self, path: str) -> bool:
        """
        Returns true iff the file at ``path`` exists in the resource.

        :param str path: a relative ``/``-separated path that does not end with
            a ``/``
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
    def get_file_digest(self, path: str, algorithm: str) -> str:
        """
        Returns a hexdigest of the contents of the file at ``path`` computed
        using the digest algorithm ``algorithm``.

        :param str path: a relative ``/``-separated path
        :param str algorithm: the name of the digest algorithm to use, as
            recognized by `hashlib`
        :rtype: str
        """
        ...

    @overload
    def open(
        self,
        path: str,
        encoding: None = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO[bytes]:
        ...

    @overload
    def open(
        self,
        path: str,
        encoding: str,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> TextIO:
        ...

    @abc.abstractmethod
    def open(
        self,
        path: str,
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO:
        """
        Returns a readable IO handle for reading the contents of the file at
        the given path.  If ``encoding`` is `None`, the handle is a binary
        handle; otherwise, it is a text handle decoded using the given
        encoding.

        :raises NoSuchFileError: if the given file does not exist
        """
        ...


class BackedDistInfo(DistInfoProvider, FileProvider):
    def verify_record(self) -> None:
        files = set(self.list_files())
        # Check everything in RECORD against actual values:
        for path, data in self.record.items():
            if path.endswith("/"):
                if not self.has_directory(path):
                    raise exc.MissingFileError(path)
            elif path not in files:
                raise exc.MissingFileError(path)
            elif data is not None:
                ### TODO: What happens if the given path is backed by a
                ### directory?
                with self.open(path) as fp:
                    data.verify(fp, path)
            files.discard(path)
        # Check that the only files that aren't in RECORD are signatures:
        for path in files:
            if not is_dist_info_path(path, "RECORD.jws") and not is_dist_info_path(
                path, "RECORD.p7s"
            ):
                raise exc.ExtraFileError(path)


@attr.define
class DistInfoDir(DistInfoProvider):
    path: Path = attr.field(converter=mkpath)

    @overload
    def open_dist_info_file(
        self,
        path: str,
        encoding: None = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
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


@attr.define
class WheelFile(BackedDistInfo):
    filename: ParsedWheelFilename
    fp: IO[bytes]
    zipfile: ZipFile

    @classmethod
    def from_path(cls, path: AnyPath, strict: bool = False) -> WheelFile:
        # Recommend the use of this method in case __init__'s signature changes
        # later
        p = Path(os.fsdecode(path))
        filename = parse_wheel_filename(p)
        fp = p.open("rb")
        zipfile = ZipFile(fp)
        w = cls(filename=filename, fp=fp, zipfile=zipfile)
        if strict:
            w.dist_info_dirname
            w.data_dirname
            w.wheel_info
            w.record
            w.metadata
            w.entry_points
        return w

    def __enter__(self) -> WheelFile:
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()

    def close(self) -> None:
        if not self.closed:
            self.zipfile.close()
            self.fp.close()

    @property
    def closed(self) -> bool:
        return self.fp.closed

    @cached_property
    def dist_info_dirname(self) -> str:
        return find_special_dir(
            ".dist-info",
            self.zipfile.namelist(),
            self.filename.project,
            self.filename.version,
            required=True,
        )

    @cached_property
    def data_dirname(self) -> Optional[str]:
        return find_special_dir(
            ".data",
            self.zipfile.namelist(),
            self.filename.project,
            self.filename.version,
            required=False,
        )

    @overload
    def open_dist_info_file(
        self,
        path: str,
        encoding: None = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
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
            return self.open(
                self.dist_info_dirname + "/" + path,
                encoding=encoding,
                errors=errors,
                newline=newline,
            )
        except exc.NoSuchFileError:
            raise exc.MissingDistInfoFileError(path)

    def has_dist_info_file(self, path: str) -> bool:
        return self.has_file(self.dist_info_dirname + "/" + path)

    def list_files(self) -> List[str]:
        return [name for name in self.zipfile.namelist() if not name.endswith("/")]

    def has_directory(self, path: str) -> bool:
        if not path.endswith("/"):
            path += "/"
        if path == "/":  # This is the only time `path` can be absolute.
            return True
        return any(name.startswith(path) for name in self.zipfile.namelist())

    def has_file(self, path: str) -> bool:
        try:
            self.zipfile.getinfo(path)
        except KeyError:
            return False
        else:
            return True

    def get_file_size(self, path: str) -> int:
        return self.zipfile.getinfo(path).file_size

    def get_file_digest(self, path: str, algorithm: str) -> str:
        with self.open(path) as fp:
            digest = digest_file(fp, [algorithm])[0][algorithm]
        return digest

    @overload
    def open(
        self,
        path: str,
        encoding: None = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO[bytes]:
        ...

    @overload
    def open(
        self,
        path: str,
        encoding: str,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> TextIO:
        ...

    def open(
        self,
        path: str,
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO:
        try:
            zi = self.zipfile.getinfo(path)
        except KeyError:
            raise exc.NoSuchFileError(path)
        fp = self.zipfile.open(zi)
        if encoding is not None:
            return io.TextIOWrapper(
                fp, encoding=encoding, errors=errors, newline=newline
            )
        else:
            return fp
