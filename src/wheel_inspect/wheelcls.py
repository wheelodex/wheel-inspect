from   cgi                 import parse_header
import io
import os.path
from   zipfile             import ZipFile
from   pkg_resources       import EntryPoint, yield_lines
from   property_manager    import cached_property
from   readme_renderer.rst import render
from   .                   import errors
from   .errors             import WheelValidationError
from   .filename           import parse_wheel_filename
from   .metadata           import parse_metadata
from   .record             import Record
from   .util               import digest_file, extract_modules, \
                                    split_keywords, unique_projects
from   .wheel_info         import parse_wheel_info

def parse_entry_points(fp):
    return {
        gr: {
            k: {
                "module": e.module_name,
                "attr": '.'.join(e.attrs) if e.attrs else None,
                "extras": list(e.extras),
            } for k,e in eps.items()
        } for gr, eps in EntryPoint.parse_map(fp).items()
    }

def readlines(fp):
    return list(yield_lines(fp))

EXTRA_DIST_INFO_FILES = [
    # file name, handler function, result dict key
    # <https://setuptools.readthedocs.io/en/latest/formats.html>:
    ('dependency_links.txt', readlines, 'dependency_links'),
    ('entry_points.txt', parse_entry_points, 'entry_points'),
    ('namespace_packages.txt', readlines, 'namespace_packages'),
    ('top_level.txt', readlines, 'top_level'),
]

class Wheel:
    def __init__(self, path):
        self.path = path
        self.parsed_filename = parse_wheel_filename(os.path.basename(path))
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

    @cached_property
    def record(self):
        rec = self._get_dist_info('RECORD')
        if rec is None:
            raise errors.MissingRecordError()
        with self.zipfile.open(rec) as fp:
            # The csv module requires this file to be opened with `newline=''`
            return Record.load(io.TextIOWrapper(fp, 'utf-8', newline=''))

    def verify_record(self):
        # Check everything in RECORD against actual values:
        for entry in self.record:
            if entry:
                entry.verify(self.zipfile)
            elif entry.path != self.dist_info + '/RECORD':
                raise errors.NullEntryError(entry.path)
        # Check everything in zipfile appears in RECORD (except signatures and
        # directories):
        for path in self.zipfile.namelist():
            if path not in self.record and path not in (
                self.dist_info + '/RECORD.jws',
                self.dist_info + '/RECORD.p7s',
            ) and not path.endswith('/'):
                raise errors.ExtraFileError(path)

    @cached_property
    def metadata(self):
        rec = self._get_dist_info('METADATA')
        if rec is None:
            ### TODO: This should be an error
            return None
        with self.zipfile.open(rec) as fp:
            return parse_metadata(io.TextIOWrapper(fp, 'utf-8'))

    @cached_property
    def wheel_info(self):
        rec = self._get_dist_info('WHEEL')
        if rec is None:
            ### TODO: This should be an error
            return None
        with self.zipfile.open(rec) as fp:
            return parse_wheel_info(io.TextIOWrapper(fp, 'utf-8'))

    def _get_dist_info(self, filename):
        try:
            return self.zipfile.getinfo(self.dist_info + '/' + filename)
        except KeyError:
            return None

    def inspect(self):
        namebits = self.parsed_filename
        about = {
            "filename": os.path.basename(self.path),
            "project": namebits.project,
            "version": namebits.version,
            "buildver": namebits.build,
            "pyver": namebits.python_tags,
            "abi": namebits.abi_tags,
            "arch": namebits.platform_tags,
        }
        try:
            record = self.record
        except WheelValidationError as e:
            record = None
            about["valid"] = False
            about["validation_error"] = {
                "type": type(e).__name__,
                "str": str(e),
            }
        else:
            try:
                self.verify_record()
            except WheelValidationError as e:
                about["valid"] = False
                about["validation_error"] = {
                    "type": type(e).__name__,
                    "str": str(e),
                }
            else:
                about["valid"] = True

        about["file"] = {"size": os.path.getsize(self.path)}
        self.fp.seek(0)
        about["file"]["digests"] = digest_file(self.fp, ["md5", "sha256"])

        about["dist_info"] = {}
        if self.metadata is not None:
            about["dist_info"]["metadata"] = self.metadata
        if record is not None:
            about["dist_info"]["record"] = record.for_json()
        if self.wheel_info is not None:
            about["dist_info"]["wheel"] = self.wheel_info

        for fname, parser, key in EXTRA_DIST_INFO_FILES:
            info = self._get_dist_info(fname)
            if info is not None:
                with self.zipfile.open(info) as fp:
                    about["dist_info"][key] = parser(io.TextIOWrapper(fp, 'utf-8'))

        if self._get_dist_info('zip-safe') is not None:
            about["dist_info"]["zip_safe"] = True
        elif self._get_dist_info('not-zip-safe') is not None:
            about["dist_info"]["zip_safe"] = False

        md = about["dist_info"].get("metadata", {})
        about["derived"] = {
            "description_in_body": "BODY" in md,
            "description_in_headers": "description" in md,
        }

        if "BODY" in md and "description" not in md:
            md["description"] = md["BODY"]
        md.pop("BODY", None)
        readme = md.get("description")
        if readme is not None:
            md["description"] = {"length": len(md["description"])}
            dct = md.get("description_content_type")
            if dct is None or parse_header(dct)[0] == 'text/x-rst':
                about["derived"]["readme_renders"] = render(readme) is not None
            else:
                about["derived"]["readme_renders"] = True
        else:
            about["derived"]["readme_renders"] = None

        if md.get("keywords") is not None:
            about["derived"]["keywords"], about["derived"]["keyword_separator"] \
                = split_keywords(md["keywords"])
        else:
            about["derived"]["keywords"], about["derived"]["keyword_separator"] \
                = [], None
        about["derived"]["keywords"] = sorted(set(about["derived"]["keywords"]))

        about["derived"]["dependencies"] = sorted(unique_projects(
            req["name"] for req in md.get("requires_dist", [])
        ))

        about["derived"]["modules"] = extract_modules([
            rec["path"] for rec in about["dist_info"].get("record", [])
        ])

        return about

def inspect_wheel(path):
    """
    Examine the Python wheel at the given path and return various information
    about the contents within as a JSON-serializable `dict`
    """
    with Wheel(path) as whl:
        return whl.inspect()
