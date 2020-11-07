from   email.message   import EmailMessage
import hashlib
from   keyword         import iskeyword
import re
from   typing          import List, Optional, Tuple
from   packaging.utils import canonicalize_name, canonicalize_version
from   .errors         import DistInfoError

DIGEST_CHUNK_SIZE = 65535

DIST_INFO_DIR_RGX = re.compile(
    r'[A-Za-z0-9](?:[A-Za-z0-9._]*[A-Za-z0-9])?-[A-Za-z0-9_.!+]+\.dist-info'
)

DATA_DIR_RGX = re.compile(
    r'[A-Za-z0-9](?:[A-Za-z0-9._]*[A-Za-z0-9])?-[A-Za-z0-9_.!+]+\.data'
)

# <https://discuss.python.org/t/identifying-parsing-binary-extension-filenames/>
MODULE_EXT_RGX = re.compile(
    r'(?<=.)\.(?:py|pyd|so|[-A-Za-z0-9_]+\.(?:pyd|so))\Z'
)

def extract_modules(filelist):
    modules = set()
    for fname in filelist:
        parts = fname.split('/')
        if not parts:
            continue
        if len(parts) > 2 and is_data_dir(parts[0]) \
                and parts[1] in ('purelib', 'platlib'):
            parts = parts[2:]
        m = MODULE_EXT_RGX.search(parts[-1])
        if m is None:
            continue
        parts[-1] = parts[-1][:m.start()]
        if not all(p.isidentifier() and not iskeyword(p) for p in parts):
            continue
        if parts[-1] == '__init__' and len(parts) > 1:
            parts.pop()
        modules.add('.'.join(parts))
    return sorted(modules)

def split_keywords(kwstr):
    # cf. `format_tags()` in Warehouse <https://git.io/fA1AT>, which seems to
    # be the part of PyPI responsible for splitting keywords up for display

    # cf. how wheel handles keywords:
    #keywords = re.split(r'[\0-,]+', kwstr)

    # Based on how pydigger.com seems to handle keywords (See
    # <https://pydigger.com/keywords>):
    if ',' in kwstr:
        return ([k for k in map(str.strip, kwstr.split(',')) if k], ',')
    else:
        return (kwstr.split(), ' ')

def strfield(s):
    return None if s is None or s.strip() in ('', 'UNKNOWN') else s

def fieldnorm(s):
    return s.lower().replace('-', '_')

def unique_projects(projects):
    seen = set()
    for p in projects:
        pn = canonicalize_name(p)
        if pn not in seen:
            yield p
        seen.add(pn)

def digest_file(fp, algorithms):
    digests = {alg: getattr(hashlib, alg)() for alg in algorithms}
    for chunk in iter(lambda: fp.read(DIGEST_CHUNK_SIZE), b''):
        for d in digests.values():
            d.update(chunk)
    return {k: v.hexdigest() for k,v in digests.items()}

def split_content_type(s):
    msg = EmailMessage()
    msg["Content-Type"] = s
    ct = msg["Content-Type"]
    return (ct.maintype, ct.subtype, ct.params)

def is_dist_info_dir(name):
    return DIST_INFO_DIR_RGX.fullmatch(name) is not None

def is_data_dir(name):
    return DATA_DIR_RGX.fullmatch(name) is not None

def is_dist_info_path(path, name):
    pre, _, post = path.partition('/')
    return is_dist_info_dir(pre) and post == name

def yield_lines(fp):
    # Like pkg_resources.yield_lines(fp), but without the dependency on
    # pkg_resources
    for line in fp:
        line = line.strip()
        if line and not line.startswith('#'):
            yield line

def find_dist_info_dir(namelist: List[str], project: str, version: str) \
        -> Tuple[str, Optional[str]]:
    """
    Given a list ``namelist`` of files in a wheel for a project ``project`` and
    version ``version``, find & return the name of the wheel's ``.dist-info``
    directory.

    :raises DistInfoError: if there is no unique ``.dist-info`` directory in
        the input
    :raises DistInfoError: if the name & version of the ``.dist-info``
        directory are not normalization-equivalent to ``project`` & ``version``
    """
    canon_project = canonicalize_name(project)
    canon_version = canonicalize_version(version.replace('_', '-'))
    dist_info_dirs = set()
    for n in namelist:
        basename = n.rstrip('/').split('/')[0]
        if is_dist_info_dir(basename):
            dist_info_dirs.add(basename)
    if len(dist_info_dirs) > 1:
        raise DistInfoError('Wheel contains multiple .dist-info directories')
    elif len(dist_info_dirs) == 1:
        dist_info_dir = next(iter(dist_info_dirs))
        diname, _, diversion = dist_info_dir[:-len(".dist-info")].partition('-')
        if (
            canonicalize_name(diname) != canon_project
            or canonicalize_version(diversion.replace('_', '-'))
                != canon_version
        ):
            raise DistInfoError(
                f"Project & version of wheel's .dist-info directory do not"
                f" match wheel name: {dist_info_dir!r}"
            )
        return dist_info_dir
    else:
        raise DistInfoError('No .dist-info directory in wheel')
