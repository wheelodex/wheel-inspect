from   email.message   import EmailMessage
import hashlib
from   keyword         import iskeyword
import re
from   packaging.utils import canonicalize_name as normalize

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
        pn = normalize(p)
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
