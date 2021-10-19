from __future__ import annotations
import abc
from io import TextIOWrapper
import os
import pathlib
import sys
from typing import (
    IO,
    Any,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Set,
    TextIO,
    Tuple,
    TypeVar,
    Union,
    overload,
)
from zipfile import ZipFile
import attr
from entry_points_txt import EntryPointSet
from entry_points_txt import load as load_entry_points
from iterpath import iterpath
from wheel_filename import ParsedWheelFilename, parse_wheel_filename
from . import errors as exc
from .bases import Path
from .consts import AnyPath, PathType, Tree
from .metadata import parse_metadata
from .record import FileData, Record, RecordPath
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


FiletreeID = Union[Tree, str]  # str = folder under .data

T = TypeVar("T", bound="DistInfoProvider")

P = TypeVar("P", bound="TreePath")


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

    @cached_property
    def filetrees(self) -> FiletreeMapping:
        return FiletreeMapping(
            record=self.record, root_is_purelib=self.wheel_info["root_is_purelib"]
        )


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
        path: Union[str, RecordPath, TreePath],
        mode: Literal["r"] = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> TextIO:
        ...

    @overload
    def open(
        self,
        path: Union[str, RecordPath, TreePath],
        mode: Literal["rb"],
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> IO[bytes]:
        ...

    @abc.abstractmethod
    def open(
        self,
        path: Union[str, RecordPath, TreePath],
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
        # We deliberately do not check directories for inclusion in the RECORD.
        # See <https://github.com/pypa/wheel/pull/289>.
        files = set(self.list_files())
        for path in record:
            self.verify_file(record.filetree / path, digest=digest)
            files.discard(path)
        # Check that the only files that aren't in RECORD are signatures:
        for path in files:
            if not is_signature_file(path):
                raise exc.UnrecordedPathError(path)

    def verify_file(
        self, path: Union[RecordPath, TreePath], digest: bool = True
    ) -> None:
        rpath = path  # For readability
        spath = str(rpath)
        filedata = rpath.filedata
        if not rpath.exists():
            # The path isn't in RECORD; now we check whether it should be.
            if is_signature_file(spath):
                return
            try:
                ptype = self.get_path_type(spath)
            except exc.NoSuchPathError:
                # The path doesn't exist, so the lack of an entry in RECORD is
                # correct.
                return
            if ptype != PathType.DIRECTORY:
                # Directories don't need RECORD entries.  PathType.OTHER nodes
                # don't belong in dist-info backings, so we definitely should
                # raise some sort of error for them; for now, we just complain
                # that they're not in the RECORD (not that they can be).
                raise exc.UnrecordedPathError(spath)
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
    path: pathlib.Path

    @classmethod
    def from_path(cls, path: AnyPath, strict: bool = True) -> DistInfoDir:
        d = cls(pathlib.Path(os.fsdecode(path)))
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
        except IsADirectoryError:
            raise exc.NotFileError(path)

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

    @cached_property
    def filetrees(self) -> BackedFiletreeMapping:  # type: ignore[override]
        return BackedFiletreeMapping(
            record=self.record,
            root_is_purelib=self.wheel_info["root_is_purelib"],
            backing=self,
        )

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

    def verify_file(
        self, path: Union[str, RecordPath, TreePath], digest: bool = True
    ) -> None:
        if isinstance(path, str):
            path = self.record.filetree / path
        super().verify_file(path, digest=digest)


@attr.define
class WheelFile(BackedDistInfo):
    # __init__ is not for public use; users should use one of the classmethods
    # to construct instances
    fp: Optional[IO[bytes]]
    zipfile: ZipFile
    closed: bool = attr.field(default=False, init=False)
    _fp_from_user: bool = False

    @classmethod
    def from_file(
        cls, file: Union[AnyPath, IO[bytes]], strict: bool = True
    ) -> WheelFile:
        filename: Optional[str]
        fp: IO[bytes]
        if isinstance(file, (str, bytes, os.PathLike)):
            filename = os.fsdecode(file)
            fp = open(filename, "rb")
            fp_from_user = False
        else:
            filename = getattr(file, "name", None)
            fp = file
            fp_from_user = True
        name: Optional[ParsedWheelFilename]
        if filename is not None:
            # TODO: Should this be allowed to fail when `file` is a file
            # object?
            name = parse_wheel_filename(filename)
        else:
            name = None
        w = cls(wheel_name=name, fp=fp, zipfile=ZipFile(fp), fp_from_user=fp_from_user)
        if strict:
            w.validate()
        return w

    @classmethod
    def from_zipfile(cls, zipfile: ZipFile, strict: bool = True) -> WheelFile:
        name: Optional[ParsedWheelFilename]
        if zipfile.filename is not None:
            # TODO: Should this be allowed to fail?
            name = parse_wheel_filename(zipfile.filename)
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
            if self.fp is not None and not self._fp_from_user:
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
            zi = self.zipfile.getinfo(path)
        except KeyError:
            raise exc.NoSuchPathError(path)
        if zi.is_dir():
            raise exc.NotFileError(path)
        return zi.file_size

    @overload
    def open(
        self,
        path: Union[str, RecordPath, TreePath],
        mode: Literal["r"] = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> TextIO:
        ...

    @overload
    def open(
        self,
        path: Union[str, RecordPath, TreePath],
        mode: Literal["rb"],
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> IO[bytes]:
        ...

    def open(
        self,
        path: Union[str, RecordPath, TreePath],
        mode: Literal["r", "rb"] = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO:
        if mode not in ("r", "rb"):
            raise ValueError(f"Unsupported file mode: {mode!r}")
        if not isinstance(path, str):
            if path.is_dir():
                # Don't raise NotFileError yet; NoSuchPathError might be more
                # accurate
                path = str(path) + "/"
            else:
                path = str(path)
        try:
            zi = self.zipfile.getinfo(path)
        except KeyError:
            raise exc.NoSuchPathError(path)
        if zi.is_dir():
            raise exc.NotFileError(path)
        fp = self.zipfile.open(zi)
        if mode == "r":
            return TextIOWrapper(fp, encoding=encoding, errors=errors, newline=newline)
        else:
            return fp


@attr.define
class UnpackedWheelDir(BackedDistInfo):
    # This follows symlinks … for now
    path: pathlib.Path

    @classmethod
    def from_path(
        cls, path: AnyPath, wheel_name: Optional[str], strict: bool = True
    ) -> UnpackedWheelDir:
        name: Optional[ParsedWheelFilename]
        if wheel_name is not None:
            name = parse_wheel_filename(wheel_name)
        else:
            name = None
        w = cls(wheel_name=name, path=pathlib.Path(os.fsdecode(path)))
        if strict:
            w.validate()
        return w

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
        ### TODO: Do something if path.startswith("/") or path == ""
        p = self.path / path
        if not p.exists():
            raise exc.NoSuchPathError(path)
        elif p.is_dir():
            return PathType.DIRECTORY
        elif p.is_file():
            return PathType.FILE
        else:
            return PathType.OTHER

    def list_files(self) -> List[str]:
        # We need to use a function with an explicit `os.DirEntry[str]`
        # annotation because just using `filter=os.DirEntry.is_file` gives a
        # typing error.
        def filterer(e: os.DirEntry[str]) -> bool:
            return e.is_file()

        return [
            str(p.relative_to(self.path))
            for p in iterpath(
                self.path, dirs=False, followlinks=True, filter_files=filterer
            )
        ]

    def list_top_level_dirs(self) -> List[str]:
        # TODO: Should the results have trailing slashes or not?
        return [p.name for p in self.path.iterdir() if p.is_dir()]

    def has_directory(self, path: str) -> bool:
        if path == "/":  # This is the only time `path` can be absolute.
            return True
        ### TODO: Do something if path.startswith("/") or path == ""
        return (self.path / path).is_dir()

    def has_file(self, path: str) -> bool:
        ### TODO: Do something if path.startswith("/") or path == ""
        return (self.path / path).is_file()

    def get_file_size(self, path: str) -> int:
        ### TODO: Do something if path.startswith("/") or path == ""
        p = self.path / path
        if not p.is_file():
            raise exc.NotFileError(path)
        try:
            return p.stat().st_size
        except FileNotFoundError:
            raise exc.NoSuchPathError(path)

    @overload
    def open(
        self,
        path: Union[str, RecordPath, TreePath],
        mode: Literal["r"] = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> TextIO:
        ...

    @overload
    def open(
        self,
        path: Union[str, RecordPath, TreePath],
        mode: Literal["rb"],
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> IO[bytes]:
        ...

    def open(
        self,
        path: Union[str, RecordPath, TreePath],
        mode: Literal["r", "rb"] = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO:
        if mode not in ("r", "rb"):
            raise ValueError(f"Unsupported file mode: {mode!r}")
        # If path.is_dir(), don't raise NotFileError yet; NoSuchPathError might
        # be more accurate
        path = str(path)
        ### TODO: Do something if path.startswith("/") or path == ""
        p = self.path / path
        try:
            # We can't do `p.open("r", ...)` for mode="r", as Path.open()
            # doesn't support `newline`.
            fp = p.open("rb")
        except FileNotFoundError:
            raise exc.NoSuchPathError(path)
        except IsADirectoryError:
            raise exc.NotFileError(path)
        if mode == "r":
            return TextIOWrapper(fp, encoding=encoding, errors=errors, newline=newline)
        else:
            return fp


@attr.define
class TreePath(Path):
    # .parts and str() contain the full path from the root of the wheel, not
    # from the root of the filetree

    tree_id: FiletreeID

    # For ROOT/<root>lib, this is pruned of the .dist-info and .data trees
    _record_path: RecordPath

    # How many leading path components to strip from .path to get the parts
    # relative to the root of the filetree
    _root_depth: int

    def __repr__(self) -> str:
        if isinstance(self.tree_id, Tree):
            tree = str(self.tree_id)
        else:
            tree = repr(self.tree_id)
        return f"{type(self).__name__}({str(self)!r}, tree_id={tree})"

    @property
    def filedata(self) -> Optional[FileData]:
        return self._record_path.filedata

    @property
    def relative_parts(self) -> Tuple[str, ...]:
        # Relative to the root of the tree
        return self.parts[self._root_depth :]

    @property
    def relative_path(self) -> str:
        # Relative to the root of the tree
        return "/".join(self.relative_parts)

    def get_subpath(self: P, name: str) -> P:
        if self.is_file():
            raise exc.NotDirectoryError(str(self))
        elif name == ".":
            return self
        elif name == "..":
            return self.parent
        else:
            subnode = self._record_path / name
            return attr.evolve(self, parts=subnode.parts, record_path=subnode)

    @property
    def parent(self: P) -> P:
        if self.is_root():
            return self
        else:
            supernode = self._record_path.parent
            return attr.evolve(self, parts=supernode.parts, record_path=supernode)

    def is_root(self) -> bool:
        # Detects whether we're at the root of the filetree
        return len(self.parts) == self._root_depth

    @property
    def path_type(self) -> PathType:
        return self._record_path.path_type

    def exists(self) -> bool:
        return self._record_path.exists()

    def is_file(self) -> bool:
        return self._record_path.is_file()

    def is_dir(self) -> bool:
        return self._record_path.is_dir()

    def iterdir(self: P) -> Iterator[P]:
        for n in self._record_path.iterdir():
            yield attr.evolve(self, parts=n.parts, record_path=n)


# Need to be explicit because we're inheriting a __repr__:
@attr.define(repr=False)
class BackedTreePath(TreePath):
    backing: BackedDistInfo

    @overload
    def open(
        self,
        mode: Literal["r"] = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> TextIO:
        ...

    @overload
    def open(
        self,
        mode: Literal["rb"],
        encoding: None = None,
        errors: None = None,
        newline: None = None,
    ) -> IO[bytes]:
        ...

    def open(
        self,
        mode: Literal["r", "rb"] = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        newline: Optional[str] = None,
    ) -> IO:
        if mode not in ("r", "rb"):
            raise ValueError(f"Unsupported file mode: {mode!r}")
        if mode == "r":
            return self.backing.open(
                self,
                mode=mode,
                encoding=encoding,
                errors=errors,
                newline=newline,
            )
        else:
            return self.backing.open(self, mode=mode)

    def read_bytes(self) -> bytes:
        with self.open("rb") as fp:
            return fp.read()

    def read_text(
        self, encoding: Optional[str] = None, errors: Optional[str] = None
    ) -> str:
        with self.open("r", encoding=encoding, errors=errors) as fp:
            return fp.read()

    def verify(self, digest: bool = True) -> None:
        if not self.exists():
            ### TODO: Replace this with a different exception:
            raise exc.NoSuchPathError(str(self))
        else:
            self.backing.verify_file(self._record_path, digest=digest)


@attr.define
class FiletreeMapping(Mapping[FiletreeID, TreePath]):
    record: Record
    root_is_purelib: bool
    _cache: Dict[FiletreeID, TreePath] = attr.field(factory=dict, init=False)

    # When root-is-purelib, Tree.PLATLIB and "platlib" are the same (because
    # the latter just accesses the *.data subdir of that name), but "purelib"
    # does not exist (unless the wheel actually has a *.data/purelib directory)
    def __getitem__(self, key: FiletreeID) -> TreePath:
        rkey = self._resolve_key(key)
        if rkey not in self._cache:
            root = self._get_root(rkey)
            if root is None:
                raise KeyError(key)
            self._cache[rkey] = TreePath(
                parts=root.parts,
                tree_id=rkey,
                record_path=root,
                root_depth=len(root.parts),
            )
        return self._cache[rkey]

    def __iter__(self) -> Iterator[FiletreeID]:
        keys: Set[FiletreeID] = set(map(self._resolve_key, Tree))
        data_dirname = self.record.data_dirname
        if data_dirname is not None:
            data_dir = self.record.filetree / data_dirname
            if self.root_is_purelib and not (data_dir / "platlib").exists():
                keys.discard(Tree.PLATLIB)
            elif not self.root_is_purelib and not (data_dir / "purelib").exists():
                keys.discard(Tree.PURELIB)
            for p in data_dir.iterdir():
                if p.is_dir():
                    keys.add(self._resolve_key(p.name))
        return iter(keys)

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def _resolve_key(self, key: FiletreeID) -> FiletreeID:
        if key is Tree.ROOT:
            if self.root_is_purelib:
                return Tree.PURELIB
            else:
                return Tree.PLATLIB
        elif not key or (isinstance(key, str) and "/" in key) or key in (".", ".."):
            raise KeyError(key)
        else:
            return key

    def _get_root(self, tree_id: FiletreeID) -> Optional[RecordPath]:
        data_dirname = self.record.data_dirname
        if tree_id is Tree.ALL:
            root = self.record.filetree
        elif (tree_id is Tree.PURELIB and self.root_is_purelib) or (
            tree_id is Tree.PLATLIB and not self.root_is_purelib
        ):
            pruned = [self.record.dist_info_dirname]
            if data_dirname is not None:
                pruned.append(data_dirname)
            root = self.record.filetree._prune(pruned)
        elif tree_id is Tree.DIST_INFO:
            root = self.record.filetree / self.record.dist_info_dirname
        elif tree_id is Tree.DATA:
            if data_dirname is None:
                return None
            root = self.record.filetree / data_dirname
        elif data_dirname is None:
            return None
        else:
            root = (
                self.record.filetree
                / data_dirname
                / (tree_id if isinstance(tree_id, str) else tree_id.value)
            )
            if not root.is_dir():
                return None
        return root


@attr.define
class BackedFiletreeMapping(FiletreeMapping, Mapping[FiletreeID, BackedTreePath]):
    backing: BackedDistInfo

    def __getitem__(self, key: FiletreeID) -> TreePath:
        rkey = self._resolve_key(key)
        if rkey not in self._cache:
            root = self._get_root(rkey)
            if root is None:
                raise KeyError(key)
            self._cache[rkey] = BackedTreePath(
                parts=root.parts,
                tree_id=rkey,
                record_path=root,
                root_depth=len(root.parts),
                backing=self.backing,
            )
        tp = self._cache[rkey]
        assert isinstance(tp, BackedTreePath)
        return tp
