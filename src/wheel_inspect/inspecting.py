import io
from   pkg_resources       import EntryPoint, yield_lines
from   readme_renderer.rst import render
from   .                   import errors
from   .classes            import DistInfoDir, FileProvider, WheelFile
from   .util               import extract_modules, is_dist_info_path, \
                                    split_content_type, split_keywords, \
                                    unique_projects

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

def inspect(obj):  # (DistInfoProvider) -> dict
    about = obj.basic_metadata()
    about["dist_info"] = {}
    about["valid"] = True

    try:
        record = obj.get_record()
    except errors.WheelValidationError as e:
        about["valid"] = False
        about["validation_error"] = {
            "type": type(e).__name__,
            "str": str(e),
        }
    else:
        about["dist_info"]["record"] = record.for_json()
        if isinstance(obj, FileProvider):
            try:
                verify_record(obj, record)
            except errors.WheelValidationError as e:
                about["valid"] = False
                about["validation_error"] = {
                    "type": type(e).__name__,
                    "str": str(e),
                }

    try:
        metadata = obj.get_metadata()
    except errors.WheelValidationError as e:
        metadata = {}
        about["valid"] = False
        about["validation_error"] = {
            "type": type(e).__name__,
            "str": str(e),
        }
    else:
        about["dist_info"]["metadata"] = metadata

    try:
        about["dist_info"]["wheel"] = obj.get_wheel_info()
    except errors.WheelValidationError as e:
        about["valid"] = False
        about["validation_error"] = {
            "type": type(e).__name__,
            "str": str(e),
        }

    for fname, parser, key in EXTRA_DIST_INFO_FILES:
        try:
            with obj.open_dist_info_file(fname) as binfp, \
                    io.TextIOWrapper(binfp, 'utf-8') as txtfp:
                about["dist_info"][key] = parser(txtfp)
        except errors.MissingDistInfoFileError:
            pass

    if obj.has_dist_info_file('zip-safe'):
        about["dist_info"]["zip_safe"] = True
    elif obj.has_dist_info_file('not-zip-safe'):
        about["dist_info"]["zip_safe"] = False

    about["derived"] = {
        "description_in_body": "BODY" in metadata,
        "description_in_headers": "description" in metadata,
    }

    if "BODY" in metadata and "description" not in metadata:
        metadata["description"] = metadata["BODY"]
    metadata.pop("BODY", None)
    readme = metadata.get("description")
    if readme is not None:
        metadata["description"] = {"length": len(metadata["description"])}
        dct = metadata.get("description_content_type")
        if dct is None or split_content_type(dct)[:2] == ('text', 'x-rst'):
            about["derived"]["readme_renders"] = render(readme) is not None
        else:
            about["derived"]["readme_renders"] = True
    else:
        about["derived"]["readme_renders"] = None

    if metadata.get("keywords") is not None:
        about["derived"]["keywords"], about["derived"]["keyword_separator"] \
            = split_keywords(metadata["keywords"])
    else:
        about["derived"]["keywords"], about["derived"]["keyword_separator"] \
            = [], None
    about["derived"]["keywords"] = sorted(set(about["derived"]["keywords"]))

    about["derived"]["dependencies"] = sorted(unique_projects(
        req["name"] for req in metadata.get("requires_dist", [])
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
    with WheelFile(path) as wf:
        return inspect(wf)

def inspect_dist_info_dir(path):
    """
    Examine the ``*.dist-info`` directory at the given path and return various
    information about the contents within as a JSON-serializable `dict`
    """
    with DistInfoDir(path) as did:
        return inspect(did)

def verify_record(fileprod: FileProvider, record):
    files = set(fileprod.list_files())
    # Check everything in RECORD against actual values:
    for entry in record:
        if entry.path.endswith('/'):
            pass
        elif entry.path not in files:
            raise errors.FileMissingError(entry.path)
        elif entry.digest is not None:
            file_size = fileprod.get_file_size(entry.path)
            if entry.size != file_size:
                raise errors.RecordSizeMismatchError(
                    entry.path,
                    entry.size,
                    file_size,
                )
            digest = fileprod.get_file_hash(entry.path, entry.digest_algorithm)
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
