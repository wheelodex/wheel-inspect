from __future__ import annotations
from typing import Any
from readme_renderer.rst import render
from . import errors
from .classes import BackedDistInfo, DistInfoDir, DistInfoProvider, WheelFile
from .consts import AnyPath
from .util import (
    extract_modules,
    for_json,
    split_content_type,
    split_keywords,
    unique_projects,
)


def inspect(obj: DistInfoProvider, digest_files: bool = True) -> dict[str, Any]:
    about: dict[str, Any] = {}
    about["dist_info"] = {}
    about["valid"] = True
    about["wheel_name"] = for_json(obj.wheel_name)
    has_dist_info = True

    try:
        record = obj.record
    except errors.WheelError as e:
        about["valid"] = False
        about["validation_error"] = for_json(e)
        has_dist_info = not isinstance(e, errors.SpecialDirError)
    else:
        about["dist_info"]["record"] = for_json(record)
        if isinstance(obj, BackedDistInfo):
            try:
                obj.verify(digest=digest_files)
            except errors.WheelError as e:
                about["valid"] = False
                about["validation_error"] = for_json(e)

    if has_dist_info:
        try:
            metadata = obj.metadata
        except errors.WheelError as e:
            metadata = {}
            about["valid"] = False
            about["validation_error"] = for_json(e)
        else:
            about["dist_info"]["metadata"] = metadata

        try:
            about["dist_info"]["wheel"] = obj.wheel_info
        except errors.WheelError as e:
            about["valid"] = False
            about["validation_error"] = for_json(e)

        about["dist_info"]["entry_points"] = for_json(obj.entry_points)
        about["dist_info"]["dependency_links"] = for_json(obj.dependency_links)
        about["dist_info"]["namespace_packages"] = for_json(obj.namespace_packages)
        about["dist_info"]["top_level"] = for_json(obj.top_level)
        about["dist_info"]["zip_safe"] = obj.zip_safe

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


def inspect_wheel(path: AnyPath, digest_files: bool = True) -> dict[str, Any]:
    """
    Examine the Python wheel at the given path and return various information
    about the contents within as a JSON-serializable `dict`.  The structure of
    the return value is described by `~wheel_inspect.schema.WHEEL_SCHEMA`.

    :param bool digest_files: If true, the files within the wheel will have
        their digests calculated in order to verify the digests listed in the
        wheel's :file:`RECORD`
    """
    with WheelFile.from_file(path, strict=False) as wf:
        return inspect(wf, digest_files=digest_files)


def inspect_dist_info_dir(path: AnyPath) -> dict[str, Any]:
    """
    Examine the :file:`*.dist-info` directory at the given path and return
    various information about the contents within as a JSON-serializable
    `dict`.  The structure of the return value is described by
    `~wheel_inspect.schema.WHEEL_SCHEMA`.
    """
    with DistInfoDir.from_path(path, strict=False) as did:
        return inspect(did)
