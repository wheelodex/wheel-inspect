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
    filedata_is_optional,
    find_special_dir,
    is_signature_file,
    yield_lines,
)
from .wheel_info import parse_wheel_info

if sys.version_info[:2] >= (3, 8):
    from functools import cached_property
    from typing import Literal
else:
    from backports.cached_property import cached_property
    from typing_extensions import Literal


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
        ### TODO: Should dependency_links, top_level, and namespace_packages
        ### also be checked here?  The only way they could go wrong is if
        ### they're not UTF-8.
        ### What about zip_safe?

    @overload
    def open_dist_info_file(
        self,
        path: str,
        mode: Literal["r"] = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> TextIO:
        ...

    @overload
    def open_dist_info_file(
        self,
        path: str,
        mode: Literal["rb"],
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> IO[bytes]:
        ...

    @abc.abstractmethod
    def open_dist_info_file(
        self,
        path: str,
        mode: Literal["r", "rb"] = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO:
        """
        Returns a readable IO handle for reading the contents of the file at
        the given path beneath the :file:`*.dist-info` directory.

        :raises NoSuchPathError: if the given file does not exist
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
        try:
            with self.open_dist_info_file("METADATA", "r", encoding="utf-8") as fp:
                return parse_metadata(fp)
        except exc.NoSuchPathError:
            raise exc.MissingDistInfoFileError("METADATA")

    @cached_property
    def record(self) -> Record:
        try:
            with self.open_dist_info_file(
                "RECORD", "r", encoding="utf-8", newline=""
            ) as fp:
                # The csv module requires this file to be opened with
                # `newline=''`
                return Record.load(fp)
        except exc.NoSuchPathError:
            raise exc.MissingDistInfoFileError("RECORD")

    @cached_property
    def wheel_info(self) -> Dict[str, Any]:
        try:
            with self.open_dist_info_file("WHEEL", "r", encoding="utf-8") as fp:
                return parse_wheel_info(fp)
        except exc.NoSuchPathError:
            raise exc.MissingDistInfoFileError("WHEEL")

    @cached_property
    def entry_points(self) -> Optional[EntryPointSet]:
        try:
            with self.open_dist_info_file(
                "entry_points.txt", "r", encoding="utf-8"
            ) as fp:
                return load_entry_points(fp)
        except exc.NoSuchPathError:
            return None

    @property
    def dependency_links(self) -> Optional[List[str]]:
        try:
            with self.open_dist_info_file(
                "dependency_links.txt", "r", encoding="utf-8"
            ) as fp:
                return list(yield_lines(fp))
        except exc.NoSuchPathError:
            return None

    @property
    def namespace_packages(self) -> Optional[List[str]]:
        try:
            with self.open_dist_info_file(
                "namespace_packages.txt", "r", encoding="utf-8"
            ) as fp:
                return list(yield_lines(fp))
        except exc.NoSuchPathError:
            return None

    @property
    def top_level(self) -> Optional[List[str]]:
        try:
            with self.open_dist_info_file("top_level.txt", "r", encoding="utf-8") as fp:
                return list(yield_lines(fp))
        except exc.NoSuchPathError:
            return None

    @property
    def zip_safe(self) -> Optional[bool]:
        ### TODO: What should happen if they're both present?
        if self.has_dist_info_file("zip-safe"):
            return True
        elif self.has_dist_info_file("not-zip-safe"):
            return False
        else:
            return None


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
        with self.open(path, "rb") as fp:
            digest = digest_file(fp, [algorithm])[algorithm]
        return digest

    @overload
    def open(
        self,
        path: Union[str, RecordPath],
        mode: Literal["r"] = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> TextIO:
        ...

    @overload
    def open(
        self,
        path: Union[str, RecordPath],
        mode: Literal["rb"],
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> IO[bytes]:
        ...

    @abc.abstractmethod
    def open(
        self,
        path: Union[str, RecordPath],
        mode: Literal["r", "rb"] = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO:
        """
        Returns a readable IO handle for reading the contents of the file at
        the given path.

        :raises NoSuchPathError: if the given file does not exist
        """
        ...

    def verify_record(self, record: Record, digest: bool = True) -> None:
        ### TODO: Verify that all directories are present in RECORD
        files = set(self.list_files())
        for path in record:
            self.verify_file(record.filetree / path, digest=digest)
            files.discard(path)
        # Check that the only files that aren't in RECORD are signatures:
        for path in files:
            if not is_signature_file(path):
                raise exc.UnrecordedPathError(path)

    def verify_file(self, path: RecordPath, digest: bool = True) -> None:
        rpath = path  # For readability
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
                if not filedata_is_optional(spath):
                    raise exc.NullEntryError(spath)
            else:
                size = self.get_file_size(spath)
                if filedata.size != size:
                    raise exc.SizeMismatchError(
                        path=spath,
                        record_size=filedata.size,
                        actual_size=size,
                    )
                if digest:
                    d = self.get_file_digest(spath, filedata.algorithm)
                    if filedata.hex_digest != d:
                        raise exc.DigestMismatchError(
                            path=spath,
                            algorithm=filedata.algorithm,
                            record_digest=filedata.hex_digest,
                            actual_digest=d,
                        )


@attr.define
class DistInfoDir(DistInfoProvider):
    path: Path

    @classmethod
    def from_path(cls, path: AnyPath, strict: bool = True) -> DistInfoDir:
        d = cls(Path(os.fsdecode(path)))
        if strict:
            d.validate()
        return d

    @overload
    def open_dist_info_file(
        self,
        path: str,
        mode: Literal["r"] = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> TextIO:
        ...

    @overload
    def open_dist_info_file(
        self,
        path: str,
        mode: Literal["rb"],
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> IO[bytes]:
        ...

    def open_dist_info_file(
        self,
        path: str,
        mode: Literal["r", "rb"] = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO:
        if mode not in ("r", "rb"):
            raise ValueError(f"Unsupported file mode: {mode!r}")
        try:
            return (self.path / path).open(
                mode, encoding=encoding, errors=errors, newline=newline
            )
        except FileNotFoundError:
            raise exc.NoSuchPathError(path)

    def has_dist_info_file(self, path: str) -> bool:
        return (self.path / path).exists()


class BackedDistInfo(DistInfoProvider, FileProvider):
    @cached_property
    def dist_info_dirname(self) -> str:
        # We can't get this one from the RECORD, as doing so would require us
        # to already know the dist-info dirname
        return find_special_dir(
            ".dist-info",
            self.list_top_level_dirs(),
            wheel_name=self.wheel_name,
            required=True,
        ).rstrip("/")

    @cached_property
    def data_dirname(self) -> Optional[str]:
        return self.record.data_dirname

    def has_dist_info_file(self, path: str) -> bool:
        return self.has_file(self.dist_info_dirname + "/" + path)

    def validate(self) -> None:
        self.dist_info_dirname
        super().validate()
        self.data_dirname
        ### TODO: Check that self.dist_info_dirname ==
        ### self.record.dist_info_dirname?  Or should that be left to
        ### verification?

    def verify(self, digest: bool = True) -> None:
        self.verify_record(self.record, digest=digest)

    def verify_file(self, path: Union[str, RecordPath], digest: bool = True) -> None:
        if not isinstance(path, RecordPath):
            path = self.record.filetree / path
        super().verify_file(path, digest=digest)


@attr.define
class WheelFile(BackedDistInfo):
    # __init__ is not for public use; users should use one of the classmethods
    # to construct instances
    fp: Optional[IO[bytes]]
    zipfile: ZipFile
    closed: bool = attr.field(default=False, init=False)

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

    @classmethod
    def from_zipfile(
        cls, zipfile: ZipFile, path: Optional[AnyPath] = None, strict: bool = True
    ) -> WheelFile:
        name: Optional[ParsedWheelFilename]
        if path is not None:
            name = parse_wheel_filename(path)
        else:
            name = None
        w = cls(wheel_name=name, fp=None, zipfile=zipfile)
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
            if self.fp is not None:
                self.fp.close()
            self.closed = True

    @overload
    def open_dist_info_file(
        self,
        path: str,
        mode: Literal["r"] = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> TextIO:
        ...

    @overload
    def open_dist_info_file(
        self,
        path: str,
        mode: Literal["rb"],
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> IO[bytes]:
        ...

    def open_dist_info_file(
        self,
        path: str,
        mode: Literal["r", "rb"] = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO:
        if mode not in ("r", "rb"):
            raise ValueError(f"Unsupported file mode: {mode!r}")
        if mode == "r":
            return self.open(
                self.dist_info_dirname + "/" + path,
                mode=mode,
                encoding=encoding,
                errors=errors,
                newline=newline,
            )
        else:
            return self.open(self.dist_info_dirname + "/" + path, mode=mode)

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
        mode: Literal["r"] = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> TextIO:
        ...

    @overload
    def open(
        self,
        path: Union[str, RecordPath],
        mode: Literal["rb"],
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> IO[bytes]:
        ...

    def open(
        self,
        path: Union[str, RecordPath],
        mode: Literal["r", "rb"] = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO:
        if mode not in ("r", "rb"):
            raise ValueError(f"Unsupported file mode: {mode!r}")
        path = str(path)
        try:
            zi = self.zipfile.getinfo(path)
        except KeyError:
            raise exc.NoSuchPathError(path)
        fp = self.zipfile.open(zi)
        if mode == "r":
            return io.TextIOWrapper(
                fp, encoding=encoding, errors=errors, newline=newline
            )
        else:
            return fp
