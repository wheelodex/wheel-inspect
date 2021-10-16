from __future__ import annotations
import abc
import io
import os
from pathlib import Path
import sys
from typing import IO, Any, Dict, List, Optional, Set, TextIO, TypeVar, Union, overload
from zipfile import ZipFile
import attr
from entry_points_txt import EntryPointSet
from entry_points_txt import load as load_entry_points
from wheel_filename import ParsedWheelFilename, parse_wheel_filename
from . import errors as exc
from .consts import AnyPath, PathType
from .metadata import parse_metadata
from .record import Record, RecordPath
from .util import (
    digest_file,
    find_special_dir,
    is_record_file,
    is_signature_file,
    mkpath,
)
from .wheel_info import parse_wheel_info

if sys.version_info[:2] >= (3, 8):
    from functools import cached_property
else:
    from cached_property import cached_property


T = TypeVar("T", bound="DistInfoProvider")


@attr.define(slots=False)  # slots=False so that cached_property works
class DistInfoProvider(abc.ABC):
    """
    An abstract class for resources that are or contain a :file:`*.dist-info`
    directory
    """

    wheel_name: Optional[ParsedWheelFilename] = attr.field(default=None, kw_only=True)

    def __enter__(self: T) -> T:
        return self

    def __exit__(self, *_exc: Any) -> Optional[bool]:
        pass

    def validate(self) -> None:
        self.wheel_info
        self.record
        self.metadata
        self.entry_points

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
    def list_top_level_dirs(self) -> List[str]:
        # TODO: Should the results have trailing slashes or not?
        ...

    @abc.abstractmethod
    def get_path_type(self, path: str) -> PathType:
        ...

    @abc.abstractmethod
    def has_directory(self, path: str) -> bool:
        """
        Returns true iff the directory at ``path`` exists in the resource.

        :param str path: a relative ``/``-separated path; trailing ``/`` is
            optional
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

    def get_file_digest(self, path: str, algorithm: str) -> str:
        """
        Returns a hexdigest of the contents of the file at ``path`` computed
        using the digest algorithm ``algorithm``.

        :param str path: a relative ``/``-separated path
        :param str algorithm: the name of the digest algorithm to use, as
            recognized by `hashlib`
        :rtype: str
        """
        with self.open(path) as fp:
            digest = digest_file(fp, [algorithm])[algorithm]
        return digest

    @overload
    def open(
        self,
        path: Union[str, RecordPath],
        encoding: None = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO[bytes]:
        ...

    @overload
    def open(
        self,
        path: Union[str, RecordPath],
        encoding: str,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> TextIO:
        ...

    @abc.abstractmethod
    def open(
        self,
        path: Union[str, RecordPath],
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO:
        """
        Returns a readable IO handle for reading the contents of the file at
        the given path.  If ``encoding`` is `None`, the handle is a binary
        handle; otherwise, it is a text handle decoded using the given
        encoding.

        :raises NoSuchPathError: if the given file does not exist
        """
        ...


@attr.define
class DistInfoDir(DistInfoProvider):
    path: Path = attr.field(converter=mkpath)

    @classmethod
    def from_path(cls, path: AnyPath, strict: bool = True) -> DistInfoDir:
        d = cls(path)
        if strict:
            d.validate()
        return d

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


class BackedDistInfo(DistInfoProvider, FileProvider):
    @cached_property
    def dist_info_dirname(self) -> str:
        return find_special_dir(
            ".dist-info",
            self.list_top_level_dirs(),
            wheel_name=self.wheel_name,
            required=True,
        ).rstrip("/")

    @cached_property
    def data_dirname(self) -> Optional[str]:
        dirname = find_special_dir(
            ".data",
            self.list_top_level_dirs(),
            wheel_name=self.wheel_name,
            required=False,
        )
        if dirname is not None:
            dirname = dirname.rstrip("/")
        return dirname

    def has_dist_info_file(self, path: str) -> bool:
        return self.has_file(self.dist_info_dirname + "/" + path)

    def validate(self) -> None:
        self.dist_info_dirname
        self.data_dirname
        super().validate()

    def verify_file(self, path: Union[str, RecordPath]) -> None:
        if isinstance(path, RecordPath):
            rpath = path
        else:
            rpath = self.record.filetree / path
        spath = str(rpath)
        filedata = rpath.filedata
        if not rpath.exists():
            if is_signature_file(spath):
                pass
            elif self.has_file(spath):
                raise exc.UnrecordedPathError(spath)
            elif self.has_directory(spath):
                raise exc.UnrecordedPathError(spath + "/")
        elif rpath.is_dir():
            try:
                ptype = self.get_path_type(spath)
            except exc.NoSuchPathError:
                raise exc.MissingPathError(spath + "/")
            if ptype != PathType.DIRECTORY:
                raise exc.PathTypeMismatchError(
                    spath,
                    record_type=PathType.DIRECTORY,
                    actual_type=ptype,
                )
        else:
            try:
                ptype = self.get_path_type(spath)
            except exc.NoSuchPathError:
                raise exc.MissingPathError(spath)
            if ptype != PathType.FILE:
                raise exc.PathTypeMismatchError(
                    spath,
                    record_type=PathType.FILE,
                    actual_type=ptype,
                )
            elif filedata is None:
                if not is_record_file(spath):
                    raise exc.NullEntryError(spath)
            else:
                size = self.get_file_size(spath)
                if filedata.size != size:
                    raise exc.SizeMismatchError(
                        path=spath,
                        record_size=filedata.size,
                        actual_size=size,
                    )
                digest = self.get_file_digest(spath, filedata.algorithm)
                if filedata.hex_digest != digest:
                    raise exc.DigestMismatchError(
                        path=spath,
                        algorithm=filedata.algorithm,
                        record_digest=filedata.hex_digest,
                        actual_digest=digest,
                    )

    def verify_record(self) -> None:
        ### TODO: Verify directories as well?
        files = set(self.list_files())
        for path in self.record:
            self.verify_file(path)
            files.discard(path)
        # Check that the only files that aren't in RECORD are signatures:
        for path in files:
            if not is_signature_file(path):
                raise exc.UnrecordedPathError(path)


@attr.define
class WheelFile(BackedDistInfo):
    # __init__ is not for public use; users should use one of the classmethods
    # to construct instances
    fp: IO[bytes]
    zipfile: ZipFile

    @classmethod
    def from_path(cls, path: AnyPath, strict: bool = True) -> WheelFile:
        p = Path(os.fsdecode(path))
        return cls.from_file(p.open("rb"), path=p, strict=strict)

    @classmethod
    def from_file(
        cls, fp: IO[bytes], path: Optional[AnyPath] = None, strict: bool = True
    ) -> WheelFile:
        name: Optional[ParsedWheelFilename]
        if path is not None:
            name = parse_wheel_filename(path)
        else:
            name = None
        w = cls(wheel_name=name, fp=fp, zipfile=ZipFile(fp))
        if strict:
            w.validate()
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
        except exc.NoSuchPathError:
            raise exc.MissingDistInfoFileError(path)

    def get_path_type(self, path: str) -> PathType:
        # We can't get the path type from zipfile.getinfo(), as that errors for
        # "implied" directories
        if self.has_directory(path):
            return PathType.DIRECTORY
        elif self.has_file(path):
            return PathType.FILE
        else:
            raise exc.NoSuchPathError(path)

    def list_files(self) -> List[str]:
        return [name for name in self.zipfile.namelist() if not name.endswith("/")]

    def list_top_level_dirs(self) -> List[str]:
        # TODO: Should the results have trailing slashes or not?
        dirs: Set[str] = set()
        for name in self.zipfile.namelist():
            name = name.strip("/")
            if name:
                dirs.add(name.split("/")[0])
        return list(dirs)

    def has_directory(self, path: str) -> bool:
        if not path.endswith("/"):
            path += "/"
        if path == "/":  # This is the only time `path` can be absolute.
            return True
        return any(name.startswith(path) for name in self.zipfile.namelist())

    def has_file(self, path: str) -> bool:
        try:
            zi = self.zipfile.getinfo(path)
        except KeyError:
            return False
        else:
            return not zi.is_dir()

    def get_file_size(self, path: str) -> int:
        try:
            return self.zipfile.getinfo(path).file_size
        except KeyError:
            raise exc.NoSuchPathError(path)

    @overload
    def open(
        self,
        path: Union[str, RecordPath],
        encoding: None = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO[bytes]:
        ...

    @overload
    def open(
        self,
        path: Union[str, RecordPath],
        encoding: str,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> TextIO:
        ...

    def open(
        self,
        path: Union[str, RecordPath],
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO:
        path = str(path)
        try:
            zi = self.zipfile.getinfo(path)
        except KeyError:
            raise exc.NoSuchPathError(path)
        fp = self.zipfile.open(zi)
        if encoding is not None:
            return io.TextIOWrapper(
                fp, encoding=encoding, errors=errors, newline=newline
            )
        else:
            return fp
