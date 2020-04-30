import abc
import io
from   pathlib        import Path
from   zipfile        import ZipFile
from   wheel_filename import parse_wheel_filename
from   .              import errors
from   .metadata      import parse_metadata
from   .record        import Record
from   .util          import digest_file
from   .wheel_info    import parse_wheel_info

class DistInfoProvider(abc.ABC):
    @abc.abstractmethod
    def basic_metadata(self):  # -> dict
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
            with self.open_dist_info_file('METADATA') as binfp, \
                    io.TextIOWrapper(binfp, 'utf-8') as txtfp:
                return parse_metadata(txtfp)
        except errors.MissingDistInfoFileError:
            raise errors.MissingMetadataError()

    def get_record(self):
        try:
            with self.open_dist_info_file('RECORD') as binfp, \
                    io.TextIOWrapper(binfp, 'utf-8', newline='') as txtfp:
                # The csv module requires this file to be opened with
                # `newline=''`
                return Record.load(txtfp)
        except errors.MissingDistInfoFileError:
            raise errors.MissingRecordError()

    def get_wheel_info(self):
        try:
            with self.open_dist_info_file('WHEEL') as binfp, \
                    io.TextIOWrapper(binfp, 'utf-8') as txtfp:
                return parse_wheel_info(txtfp)
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


class DistInfoDir(DistInfoProvider):
    def __init__(self, path):
        self.path = Path(path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def basic_metadata(self):
        return {}

    def open_dist_info_file(self, name):
        try:
            return (self.path / name).open('rb')
        except FileNotFoundError:
            raise errors.MissingDistInfoFileError(name)

    def has_dist_info_file(self, name):
        return (self.path / name).exists()


class WheelFile(DistInfoProvider, FileProvider):
    def __init__(self, path):
        self.path = Path(path)
        # We need to pass `.name` here because wheel_filename can't take Path
        # objects under Python 3.5:
        self.parsed_filename = parse_wheel_filename(self.path.name)
        self.dist_info = '{0.project}-{0.version}.dist-info'\
                            .format(self.parsed_filename)

    def __enter__(self):
        self.fp = self.path.open('rb')
        self.zipfile = ZipFile(self.fp)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.zipfile.close()
        self.fp.close()
        return False

    def basic_metadata(self):
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
