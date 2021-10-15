from typing import Any, Dict
from entry_points_txt import EntryPointSet
from readme_renderer.rst import render
from . import errors
from .classes import BackedDistInfo, DistInfoDir, DistInfoProvider, WheelFile
from .util import (
    AnyPath,
    extract_modules,
    split_content_type,
    split_keywords,
    unique_projects,
    yield_lines,
)


def jsonify_entry_points(epset: EntryPointSet) -> Dict[str, Any]:
    """
    Convert an `entry_points_txt.EntryPointSet` to a `dict` that maps entry
    point group names to sub-`dict`s that map entry point names to
    sub-sub-`dict`s with ``"module"``, ``"attr"``, and ``"extras"`` keys.

    For example, the following :file:`entry_points.txt`:

    .. code-block:: ini

        [console_scripts]
        do-thing = pkg.main:__main__

        [plugin.point]
        plug-thing = pkg.plug [xtra]

    would become the following structure::

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
    return {
        gr: {
            k: {
                "module": e.module,
                "attr": e.attr,
                "extras": list(e.extras),
            }
            for k, e in eps.items()
        }
        for gr, eps in epset.items()
    }


# <https://setuptools.readthedocs.io/en/latest/formats.html>
EXTRA_DIST_INFO_FILES = ["dependency_links", "namespace_packages", "top_level"]


def inspect(obj: DistInfoProvider, verify_files: bool = True) -> Dict[str, Any]:
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
        if isinstance(obj, BackedDistInfo) and verify_files:
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

        if obj.has_dist_info_file("entry_points.txt"):
            about["dist_info"]["entry_points"] = jsonify_entry_points(obj.entry_points)

        for key in EXTRA_DIST_INFO_FILES:
            try:
                with obj.open_dist_info_file(f"{key}.txt", encoding="utf-8") as fp:
                    about["dist_info"][key] = list(yield_lines(fp))
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


def inspect_wheel(path: AnyPath, verify_files: bool = True) -> Dict[str, Any]:
    """
    Examine the Python wheel at the given path and return various information
    about the contents within as a JSON-serializable `dict`

    :param bool verify_files: If true, the files within the wheel will have
        their digests calculated in order to verify the digests & sizes listed
        in the wheel's :file:`RECORD`
    """
    with WheelFile.from_path(path) as wf:
        return inspect(wf, verify_files=verify_files)


def inspect_dist_info_dir(path: AnyPath) -> Dict[str, Any]:
    """
    Examine the ``*.dist-info`` directory at the given path and return various
    information about the contents within as a JSON-serializable `dict`
    """
    with DistInfoDir(path) as did:
        return inspect(did)
