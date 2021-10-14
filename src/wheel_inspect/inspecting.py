import io
from typing import Any, Callable, Dict, List, TextIO, Tuple
import entry_points_txt
from readme_renderer.rst import render
from . import errors
from .classes import DistInfoDir, DistInfoProvider, WheelFile
from .util import (
    AnyPath,
    extract_modules,
    split_content_type,
    split_keywords,
    unique_projects,
    yield_lines,
)


def parse_entry_points(fp: TextIO) -> Dict[str, Any]:
    """
    Parse the contents of a text filehandle ``fp`` as an
    :file:`entry_points.txt` file and return a `dict` that maps entry point
    group names to sub-`dict`s that map entry point names to sub-sub-`dict`s
    with ``"module"``, ``"attr"``, and ``"extras"`` keys.

    For example, the following input:

    .. code-block:: ini

        [console_scripts]
        do-thing = pkg.main:__main__

        [plugin.point]
        plug-thing = pkg.plug [xtra]

    would be parsed into the following structure::

        {
            "console_scripts": {
                "do-thing": {
                    "module": "pkg.main",
                    "attr": "__main__",
                    "extras": []
                }
            },
            "plugin.point": {
                "plug-thing": {
                    "module": "pkg.plug",
                    "attr": None,
                    "extras": ["xtra"]
                }
            }
        }
    """
    epset = entry_points_txt.load(fp)
    return {
        gr: {
            k: {
                "module": e.module,
                "attr": e.object,
                "extras": list(e.extras),
            }
            for k, e in eps.items()
        }
        for gr, eps in epset.items()
    }


def readlines(fp: TextIO) -> List[str]:
    return list(yield_lines(fp))


EXTRA_DIST_INFO_FILES: List[Tuple[str, Callable[[TextIO], Any], str]] = [
    # file name, handler function, result dict key
    # <https://setuptools.readthedocs.io/en/latest/formats.html>:
    ("dependency_links.txt", readlines, "dependency_links"),
    ("entry_points.txt", parse_entry_points, "entry_points"),
    ("namespace_packages.txt", readlines, "namespace_packages"),
    ("top_level.txt", readlines, "top_level"),
]


def inspect(obj: DistInfoProvider) -> Dict[str, Any]:
    about = obj.basic_metadata()
    about["dist_info"] = {}
    about["valid"] = True
    has_dist_info = True

    try:
        record = obj.record
    except errors.WheelValidationError as e:
        about["valid"] = False
        about["validation_error"] = {
            "type": type(e).__name__,
            "str": str(e),
        }
        has_dist_info = not isinstance(e, errors.DistInfoError)
    else:
        about["dist_info"]["record"] = {
            k: v.for_json() if v is not None else None for k, v in record.items()
        }
        if isinstance(obj, WheelFile):
            try:
                obj.verify_record()
            except errors.WheelValidationError as e:
                about["valid"] = False
                about["validation_error"] = {
                    "type": type(e).__name__,
                    "str": str(e),
                }

    if has_dist_info:
        try:
            metadata = obj.metadata
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
            about["dist_info"]["wheel"] = obj.wheel_info
        except errors.WheelValidationError as e:
            about["valid"] = False
            about["validation_error"] = {
                "type": type(e).__name__,
                "str": str(e),
            }

        for fname, parser, key in EXTRA_DIST_INFO_FILES:
            try:
                with obj.open_dist_info_file(fname) as binfp, io.TextIOWrapper(
                    binfp, "utf-8"
                ) as txtfp:
                    about["dist_info"][key] = parser(txtfp)
            except errors.MissingDistInfoFileError:
                pass

        if obj.has_dist_info_file("zip-safe"):
            about["dist_info"]["zip_safe"] = True
        elif obj.has_dist_info_file("not-zip-safe"):
            about["dist_info"]["zip_safe"] = False

    else:
        metadata = {}

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
        if dct is None or split_content_type(dct)[:2] == ("text", "x-rst"):
            about["derived"]["readme_renders"] = render(readme) is not None
        else:
            about["derived"]["readme_renders"] = True
    else:
        about["derived"]["readme_renders"] = None

    if metadata.get("keywords") is not None:
        (
            about["derived"]["keywords"],
            about["derived"]["keyword_separator"],
        ) = split_keywords(metadata["keywords"])
    else:
        about["derived"]["keywords"], about["derived"]["keyword_separator"] = [], None
    about["derived"]["keywords"] = sorted(set(about["derived"]["keywords"]))

    about["derived"]["dependencies"] = sorted(
        unique_projects(req["name"] for req in metadata.get("requires_dist", []))
    )

    about["derived"]["modules"] = extract_modules(
        about["dist_info"].get("record", {}).keys()
    )

    return about


def inspect_wheel(path: AnyPath) -> Dict[str, Any]:
    """
    Examine the Python wheel at the given path and return various information
    about the contents within as a JSON-serializable `dict`
    """
    with WheelFile.from_path(path) as wf:
        return inspect(wf)


def inspect_dist_info_dir(path: AnyPath) -> Dict[str, Any]:
    """
    Examine the ``*.dist-info`` directory at the given path and return various
    information about the contents within as a JSON-serializable `dict`
    """
    with DistInfoDir(path) as did:
        return inspect(did)
