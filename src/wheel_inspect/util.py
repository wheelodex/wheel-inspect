from __future__ import annotations
from email.message import EmailMessage
import hashlib
from keyword import iskeyword
import os
from pathlib import Path
import re
import sys
from typing import (
    IO,
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    TextIO,
    Tuple,
    overload,
)
import attr
from entry_points_txt import EntryPoint
from packaging.utils import canonicalize_name
from packaging.version import Version
from wheel_filename import ParsedWheelFilename
from .consts import (
    DATA_DIR_RGX,
    DIGEST_CHUNK_SIZE,
    DIST_INFO_DIR_RGX,
    MODULE_EXT_RGX,
    PROJECT_VERSION_RGX,
    AnyPath,
)
from .errors import SpecialDirError

if sys.version_info[:2] >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


def extract_modules(filelist: Iterable[str]) -> List[str]:
    modules = set()
    for fname in filelist:
        parts = fname.split("/")
        if not parts:
            continue
        if (
            len(parts) > 2
            and is_data_dir(parts[0])
            and parts[1] in ("purelib", "platlib")
        ):
            parts = parts[2:]
        m = MODULE_EXT_RGX.search(parts[-1])
        if m is None:
            continue
        parts[-1] = parts[-1][: m.start()]
        if not all(p.isidentifier() and not iskeyword(p) for p in parts):
            continue
        if parts[-1] == "__init__" and len(parts) > 1:
            parts.pop()
        modules.add(".".join(parts))
    return sorted(modules)


def split_keywords(kwstr: str) -> Tuple[List[str], str]:
    # cf. `format_tags()` in Warehouse <https://git.io/fA1AT>, which seems to
    # be the part of PyPI responsible for splitting keywords up for display

    # cf. how wheel handles keywords:
    # keywords = re.split(r'[\0-,]+', kwstr)

    # Based on how pydigger.com seems to handle keywords (See
    # <https://pydigger.com/keywords>):
    if "," in kwstr:
        return ([k for k in map(str.strip, kwstr.split(",")) if k], ",")
    else:
        return (kwstr.split(), " ")


def strfield(s: str) -> Optional[str]:
    return None if s is None or s.strip() in ("", "UNKNOWN") else s


def fieldnorm(s: str) -> str:
    return s.lower().replace("-", "_")


def unique_projects(projects: Iterable[str]) -> Iterator[str]:
    seen = set()
    for p in projects:
        pn = canonicalize_name(p)
        if pn not in seen:
            yield p
        seen.add(pn)


def digest_file(fp: IO[bytes], algorithms: Iterable[str]) -> Dict[str, str]:
    digests = {alg: getattr(hashlib, alg)() for alg in algorithms}
    for chunk in iter(lambda: fp.read(DIGEST_CHUNK_SIZE), b""):
        for d in digests.values():
            d.update(chunk)
    return {k: v.hexdigest() for k, v in digests.items()}


def split_content_type(s: str) -> Tuple[str, str, Dict[str, str]]:
    msg = EmailMessage()
    msg["Content-Type"] = s
    ct = msg["Content-Type"]
    return (ct.maintype, ct.subtype, dict(ct.params))


def is_dist_info_dir(name: str) -> bool:
    return DIST_INFO_DIR_RGX.fullmatch(name) is not None


def is_data_dir(name: str) -> bool:
    return DATA_DIR_RGX.fullmatch(name) is not None


def is_dist_info_path(path: str, name: str) -> bool:
    pre, _, post = path.partition("/")
    return is_dist_info_dir(pre) and post == name


def yield_lines(fp: TextIO) -> Iterator[str]:
    # Like pkg_resources.yield_lines(fp), but without the dependency on
    # pkg_resources
    for line in fp:
        line = line.strip()
        if line and not line.startswith("#"):
            yield line


@overload
def find_special_dir(
    suffix: str,
    dirnames: Iterable[str],
    wheel_name: Optional[ParsedWheelFilename] = None,
    required: Literal[True] = True,
) -> str:
    ...


@overload
# Is it necessary to repeat this?
def find_special_dir(
    suffix: str,
    dirnames: Iterable[str],
    wheel_name: Optional[ParsedWheelFilename] = None,
    required: Literal[False] = False,
) -> Optional[str]:
    ...


def find_special_dir(
    suffix: str,
    dirnames: Iterable[str],
    wheel_name: Optional[ParsedWheelFilename] = None,
    required: bool = False,
) -> Optional[str]:
    """
    Given an iterable ``dirnames`` of top-level directories in a wheel (with or
    without trailing slashes), find & return the unique element of the list
    with a name of the form :samp:`{project}-{version}{suffix}`.  Typical
    values for ``suffix`` are ``".dist-info"`` and ``".data"``.

    If ``wheel_name`` is given, the found directory must use the same project &
    version as ``wheel_name`` *modulo* canonicalization.

    :raises SpecialDirError:
        - if there is more than one matching directory in the input
        - if ``required`` is true and there is no matching directory
        - if the project & version in the found directory name do not match
          ``wheel_name``
    """
    candidates: List[Tuple[str, str, str]] = []
    for n in dirnames:
        try:
            project, version = parse_special_dir(n, suffix)
        except ValueError:
            continue
        candidates.append((n, project, version))
    if len(candidates) > 1:
        raise SpecialDirError(f"Wheel contains multiple *{suffix} directories")
    elif len(candidates) == 1:
        winner, project, version = candidates[0]
        if wheel_name is not None:
            try:
                if not same_project(project, wheel_name.project) or not same_version(
                    version, wheel_name.version, unescape=True
                ):
                    raise SpecialDirError(
                        f"Project & version of wheel's *{suffix} directory do"
                        f" not match wheel name: {winner!r} vs. '{wheel_name}'"
                    )
            except ValueError:
                raise SpecialDirError(
                    f"Project or version of wheel's filename or *{suffix}"
                    f" directory is invalid: '{wheel_name}', {winner!r}"
                )
        return winner
    elif required:
        raise SpecialDirError(f"No *{suffix} directory in wheel")
    else:
        return None


def jsonify_entry_point(ep: EntryPoint) -> Dict[str, Any]:
    return {
        "module": ep.module,
        "attr": ep.attr,
        "extras": list(ep.extras),
    }


def jsonify_parsed_wheel_filename(pwf: ParsedWheelFilename) -> Dict[str, Any]:
    return {"name": str(pwf), **pwf._asdict()}


CUSTOM_JSONIFIERS: Dict[type, Callable] = {
    EntryPoint: jsonify_entry_point,
    ParsedWheelFilename: jsonify_parsed_wheel_filename,
}


def for_json(value: Any) -> Any:
    if type(value) in CUSTOM_JSONIFIERS:
        return for_json(CUSTOM_JSONIFIERS[type(value)](value))
    elif hasattr(value, "for_json"):
        return for_json(value.for_json())
    elif attr.has(value):
        return for_json(attr.asdict(value, recurse=False))
    elif isinstance(value, Mapping):
        return {k: for_json(v) for k, v in value.items()}
    elif isinstance(value, set):
        return sorted(map(for_json, value))
    elif isinstance(value, str):
        # Needs to come before Sequence or we'll get infinite recursion
        return value
    elif isinstance(value, Sequence):
        return list(map(for_json, value))
    else:
        return value


def mkpath(path: AnyPath) -> Path:
    return Path(os.fsdecode(path))


def parse_special_dir(dirname: str, suffix: str) -> Tuple[str, str]:
    n = dirname.rstrip("/")
    if not n.endswith(suffix):
        raise ValueError(f"{dirname!r} does not end in suffix {suffix!r}")
    m = re.fullmatch(PROJECT_VERSION_RGX, n[: -len(suffix)])
    if not m:
        raise ValueError(
            f"{dirname!r} is not of the form '{{project}}-{{version}}{suffix}'"
        )
    return (m["project"], m["version"])


def same_project(p1: str, p2: str) -> bool:
    return canonicalize_name(p1) == canonicalize_name(p2)


def same_version(v1: str, v2: str, unescape: bool = False) -> bool:
    if unescape:
        v1 = v1.replace("_", "-")
        v2 = v2.replace("_", "-")
    return Version(v1) == Version(v2)


def is_signature_file(path: str) -> bool:
    return is_dist_info_path(path, "RECORD.jws") or is_dist_info_path(
        path, "RECORD.p7s"
    )


def is_record_file(path: str) -> bool:
    return is_dist_info_path(path, "RECORD")
