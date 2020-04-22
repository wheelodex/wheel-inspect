import abc
import io
import os
import os.path
from   pathlib        import Path
from   zipfile        import ZipFile
from   wheel_filename import parse_wheel_filename
from   .              import errors
from   .metadata      import parse_metadata
from   .record        import Record
from   .util          import digest_file, is_dist_info_path
from   .wheel_info    import parse_wheel_info

class DistInfoProvider(abc.ABC):
    @abc.abstractmethod
    def basic_metadata(self):  # -> dict
        raise NotImplementedError

    @abc.abstractmethod
    def list_dist_info_files(self):  # -> List[str]
        raise NotImplementedError

    @abc.abstractmethod
    def open_dist_info_file(self, name):
        # returns a binary IO handle; raises MissingDistInfoFileError if file
        # does not exist
        raise NotImplementedError

    @abc.abstractmethod
    def has_dist_info_file(self, name):  # -> bool
        raise NotImplementedError

    def get_metadata(self):
        try:
            with self.open_dist_info_file('METADATA') as fp:
                return parse_metadata(io.TextIOWrapper(fp, 'utf-8'))
        except errors.MissingDistInfoFileError:
            raise errors.MissingMetadataError()

    def get_record(self):
        try:
            with self.open_dist_info_file('RECORD') as fp:
                # The csv module requires this file to be opened with
                # `newline=''`
                return Record.load(io.TextIOWrapper(fp, 'utf-8', newline=''))
        except errors.MissingDistInfoFileError:
            raise errors.MissingRecordError()

    def get_wheel_info(self):
        try:
            with self.open_dist_info_file('WHEEL') as fp:
                return parse_wheel_info(io.TextIOWrapper(fp, 'utf-8'))
        except errors.MissingDistInfoFileError:
            raise errors.MissingWheelInfoError()


class FileProvider(abc.ABC):
    @abc.abstractmethod
    def list_files(self):
        # Directories are not included
        # Uses forward slash separators
        raise NotImplementedError

    @abc.abstractmethod
    def get_file_size(self, name):
        raise NotImplementedError

    @abc.abstractmethod
    def get_file_hash(self, name, algorithm):
        # Returns a hex digest
        raise NotImplementedError

    def verify_record(self, record):
        files = set(self.list_files())
        # Check everything in RECORD against actual values:
        for entry in record:
            if entry.path.endswith('/'):
                pass
            elif entry.path not in files:
                raise errors.FileMissingError(entry.path)
            elif entry.digest is not None:
                file_size = self.get_file_size(entry.path)
                if entry.size != file_size:
                    raise errors.RecordSizeMismatchError(
                        entry.path,
                        entry.size,
                        file_size,
                    )
                digest = self.get_file_hash(entry.path, entry.digest_algorithm)
                if digest != entry.digest:
                    raise errors.RecordDigestMismatchError(
                        entry.path,
                        entry.digest_algorithm,
                        entry.digest,
                        digest,
                    )
            elif not is_dist_info_path(entry.path, 'RECORD'):
                raise errors.NullEntryError(entry.path)
            files.discard(entry.path)
        # Check that the only files that aren't in RECORD are signatures:
        for path in files:
            if not is_dist_info_path(entry.path, 'RECORD.jws') \
                    and not is_dist_info_path(entry.path, 'RECORD.p7s'):
                raise errors.ExtraFileError(path)


class DistInfoDir(DistInfoProvider):
    def __init__(self, path):
        self.path = Path(path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def basic_metadata(self):
        return {}

    def list_dist_info_files(self):
        files = []
        for dirpath, _, filenames in os.walk(str(self.path)):
            dp = Path(dirpath).relative_to(self.path)
            for f in filenames:
                files.append(str(dp / f))
        return files

    def open_dist_info_file(self, name):
        try:
            return (self.path / name).open('rb')
        except FileNotFoundError:
            raise errors.MissingDistInfoFileError(name)

    def has_dist_info_file(self, name):
        return (self.path / name).exists()


class WheelFile(DistInfoProvider, FileProvider):
    def __init__(self, path):
        self.path = path
        self.parsed_filename = parse_wheel_filename(path)
        self.dist_info = '{0.project}-{0.version}.dist-info'\
                            .format(self.parsed_filename)

    def __enter__(self):
        self.fp = open(self.path, 'rb')
        self.zipfile = ZipFile(self.fp)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.zipfile.close()
        self.fp.close()
        return False

    def basic_metadata(self):
        namebits = self.parsed_filename
        about = {
            "filename": os.path.basename(self.path),
            "project": namebits.project,
            "version": namebits.version,
            "buildver": namebits.build,
            "pyver": namebits.python_tags,
            "abi": namebits.abi_tags,
            "arch": namebits.platform_tags,
            "file": {
                "size": os.path.getsize(self.path),
            },
        }
        self.fp.seek(0)
        about["file"]["digests"] = digest_file(self.fp, ["md5", "sha256"])
        return about

    def list_dist_info_files(self):
        prefix = self.dist_info + '/'
        return [
            f[len(prefix):] for f in self.zipfile.namelist()
                            if f.startswith(prefix) and f != prefix
        ]

    def open_dist_info_file(self, name):
        try:
            zi = self.zipfile.getinfo(self.dist_info + '/' + name)
        except KeyError:
            raise errors.MissingDistInfoFileError(name)
        else:
            return self.zipfile.open(zi)

    def has_dist_info_file(self, name):  # -> bool
        try:
            self.zipfile.getinfo(self.dist_info + '/' + name)
        except KeyError:
            return False
        else:
            return True

    def list_files(self):
        return [
            name for name in self.zipfile.namelist()
                 if not name.endswith('/')
        ]

    def get_file_size(self, name):
        return self.zipfile.getinfo(name).file_size

    def get_file_hash(self, name, algorithm):
        with self.zipfile.open(name) as fp:
            return digest_file(fp, [algorithm])[algorithm]
