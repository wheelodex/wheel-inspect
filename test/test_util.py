import pytest
from   wheel_inspect.errors import DistInfoError
from   wheel_inspect.util   import extract_modules, find_dist_info_dir, \
                                    is_data_dir, is_dist_info_dir, \
                                    split_content_type, split_keywords

@pytest.mark.parametrize('kwstr,expected', [
    (
        'pypi,warehouse,search,packages,pip',
        (['pypi', 'warehouse', 'search', 'packages', 'pip'], ','),
    ),
    (
        'pypi warehouse search packages pip',
        (['pypi', 'warehouse', 'search', 'packages', 'pip'], ' '),
    ),
    (
        "pypi,pep503,simple repository api,packages,pip",
        (["pypi", "pep503", "simple repository api", "packages", "pip"], ','),
    ),
    ('', ([], ' ')),
    (' ', ([], ' ')),
    (',', ([], ',')),
    (' , ', ([], ',')),
    (' , , ', ([], ',')),
    ('foo', (['foo'], ' ')),
    ('foo,bar', (['foo', 'bar'], ',')),
    ('foo, bar', (['foo', 'bar'], ',')),
    ('foo ,bar', (['foo', 'bar'], ',')),
    (' foo , bar ', (['foo', 'bar'], ',')),
    (' foo , , bar ', (['foo', 'bar'], ',')),
    ('foo,,bar', (['foo', 'bar'], ',')),
    (',foo', (['foo'], ',')),
    ('foo,', (['foo'], ',')),
])
def test_split_keywords(kwstr, expected):
    assert split_keywords(kwstr) == expected

@pytest.mark.parametrize('filelist,modules', [
    (
        [
            "qypi/__init__.py",
            "qypi/__main__.py",
            "qypi/api.py",
            "qypi/util.py",
            "qypi-0.4.1.dist-info/DESCRIPTION.rst",
            "qypi-0.4.1.dist-info/LICENSE.txt",
            "qypi-0.4.1.dist-info/METADATA",
            "qypi-0.4.1.dist-info/RECORD",
            "qypi-0.4.1.dist-info/WHEEL",
            "qypi-0.4.1.dist-info/entry_points.txt",
            "qypi-0.4.1.dist-info/metadata.json",
            "qypi-0.4.1.dist-info/top_level.txt",
        ],
        ["qypi", "qypi.__main__", "qypi.api", "qypi.util"],
    ),

    (
        [
            "flit/__init__.py",
            "flit/__main__.py",
            "flit/_get_dirs.py",
            "flit/build.py",
            "flit/common.py",
            "flit/inifile.py",
            "flit/init.py",
            "flit/install.py",
            "flit/installfrom.py",
            "flit/log.py",
            "flit/logo.py",
            "flit/sdist.py",
            "flit/upload.py",
            "flit/wheel.py",
            "flit/license_templates/apache",
            "flit/license_templates/gpl3",
            "flit/license_templates/mit",
            "flit/vcs/__init__.py",
            "flit/vcs/git.py",
            "flit/vcs/hg.py",
            "flit/vendorized/__init__.py",
            "flit/vendorized/readme/__init__.py",
            "flit/vendorized/readme/clean.py",
            "flit/vendorized/readme/rst.py",
            "flit-0.11.1.dist-info/entry_points.txt",
            "flit-0.11.1.dist-info/LICENSE",
            "flit-0.11.1.dist-info/WHEEL",
            "flit-0.11.1.dist-info/METADATA",
            "flit-0.11.1.dist-info/RECORD",
        ],
        [
            "flit",
            "flit.__main__",
            "flit._get_dirs",
            "flit.build",
            "flit.common",
            "flit.inifile",
            "flit.init",
            "flit.install",
            "flit.installfrom",
            "flit.log",
            "flit.logo",
            "flit.sdist",
            "flit.upload",
            "flit.vcs",
            "flit.vcs.git",
            "flit.vcs.hg",
            "flit.vendorized",
            "flit.vendorized.readme",
            "flit.vendorized.readme.clean",
            "flit.vendorized.readme.rst",
            "flit.wheel",
        ],
    ),

    (
        [
            'cmarkgfm-0.4.2.dist-info/WHEEL',
            'cmarkgfm-0.4.2.dist-info/top_level.txt',
            'cmarkgfm-0.4.2.dist-info/METADATA',
            'cmarkgfm-0.4.2.dist-info/RECORD',
            'cmarkgfm/_cmark.abi3.so',
            'cmarkgfm/cmark_module.h',
            'cmarkgfm/__init__.py',
            'cmarkgfm/cmark.py',
            'cmarkgfm/build_cmark.py',
            'cmarkgfm/cmark.cffi.h',
        ],
        [
            'cmarkgfm',
            'cmarkgfm._cmark',
            'cmarkgfm.build_cmark',
            'cmarkgfm.cmark',
        ],
    ),

    (
        [
            'cmarkgfm-0.4.2.dist-info/WHEEL',
            'cmarkgfm-0.4.2.dist-info/top_level.txt',
            'cmarkgfm-0.4.2.dist-info/METADATA',
            'cmarkgfm-0.4.2.dist-info/RECORD',
            'cmarkgfm/_cmark.cp37-win_amd64.pyd',
            'cmarkgfm/cmark_module.h',
            'cmarkgfm/__init__.py',
            'cmarkgfm/cmark.py',
            'cmarkgfm/build_cmark.py',
            'cmarkgfm/cmark.cffi.h',
        ],
        [
            'cmarkgfm',
            'cmarkgfm._cmark',
            'cmarkgfm.build_cmark',
            'cmarkgfm.cmark',
        ],
    ),

    (
        [
            'cmarkgfm-0.4.2.dist-info/WHEEL',
            'cmarkgfm-0.4.2.dist-info/top_level.txt',
            'cmarkgfm-0.4.2.dist-info/METADATA',
            'cmarkgfm-0.4.2.dist-info/RECORD',
            'cmarkgfm/_cmark.so',
            'cmarkgfm/cmark_module.h',
            'cmarkgfm/__init__.py',
            'cmarkgfm/cmark.py',
            'cmarkgfm/build_cmark.py',
            'cmarkgfm/cmark.cffi.h',
        ],
        [
            'cmarkgfm',
            'cmarkgfm._cmark',
            'cmarkgfm.build_cmark',
            'cmarkgfm.cmark',
        ],
    ),

    (
        [
            'mxnet_coreml_converter-0.1.0a7.data/purelib/converter/__init__.py',
            'mxnet_coreml_converter-0.1.0a7.data/purelib/converter/_add_pooling.py',
            'mxnet_coreml_converter-0.1.0a7.data/purelib/converter/_layers.py',
            'mxnet_coreml_converter-0.1.0a7.data/purelib/converter/_mxnet_converter.py',
            'mxnet_coreml_converter-0.1.0a7.data/purelib/converter/utils.py',
            'mxnet_coreml_converter-0.1.0a7.data/scripts/mxnet_coreml_converter.py',
            'mxnet_coreml_converter-0.1.0a7.dist-info/DESCRIPTION.rst',
            'mxnet_coreml_converter-0.1.0a7.dist-info/metadata.json',
            'mxnet_coreml_converter-0.1.0a7.dist-info/top_level.txt',
            'mxnet_coreml_converter-0.1.0a7.dist-info/WHEEL',
            'mxnet_coreml_converter-0.1.0a7.dist-info/METADATA',
            'mxnet_coreml_converter-0.1.0a7.dist-info/RECORD',
        ],
        [
            'converter',
            'converter._add_pooling',
            'converter._layers',
            'converter._mxnet_converter',
            'converter.utils',
        ],
    ),

    (
        [
            '',
            'foo-1.0.data/platlib/foo/__init__.py',
            'foo-1.0.data/platlib/foo/def.py',
            'foo-1.0.data/platlib/foo/has-hyphen.py',
            'foo-1.0.data/platlib/foo/extra.ext.py',
            'foo-1.0.dist-info/METADATA',
            'foo-1.0.dist-info/WHEEL',
            'foo-1.0.dist-info/RECORD',
            'foo-1.0.dist-info/glarch.py',
        ],
        ['foo'],
    ),

    (
        [
            'Acquisition/Acquisition.h',
            'Acquisition/_Acquisition.c',
            'Acquisition/_Acquisition.pyd',
            'Acquisition/__init__.py',
            'Acquisition/interfaces.py',
            'Acquisition/tests.py',
            'Acquisition-4.6.dist-info/LICENSE.txt',
            'Acquisition-4.6.dist-info/METADATA',
            'Acquisition-4.6.dist-info/WHEEL',
            'Acquisition-4.6.dist-info/top_level.txt',
            'Acquisition-4.6.dist-info/RECORD',
        ],
        [
            'Acquisition',
            'Acquisition._Acquisition',
            'Acquisition.interfaces',
            'Acquisition.tests',
        ],
    ),

])
def test_extract_modules(filelist, modules):
    assert extract_modules(filelist) == modules

@pytest.mark.parametrize('s,ct', [
    ('text/plain', ('text', 'plain', {})),
    ('text/plain; charset=utf-8', ('text', 'plain', {"charset": "utf-8"})),
    (
        'text/markdown; charset=utf-8; variant=GFM',
        ('text', 'markdown', {"charset": "utf-8", "variant": "GFM"}),
    ),
])
def test_split_content_type(s, ct):
    assert split_content_type(s) == ct

@pytest.mark.parametrize('name,expected', [
    ('somepackage-1.0.0.dist-info', True),
    ('somepackage.dist-info', False),
    ('somepackage-1.0.0-1.dist-info', False),
    ('somepackage-1.0.0.data', False),
    ('SOME_._PaCkAgE-0.dist-info', True),
    ('foo-1!2+local.dist-info', True),
    ('foo-1_2_local.dist-info', True),
    ('.dist-info', False),
])
def test_is_dist_info_dir(name, expected):
    assert is_dist_info_dir(name) is expected

@pytest.mark.parametrize('name,expected', [
    ('somepackage-1.0.0.data', True),
    ('somepackage.data', False),
    ('somepackage-1.0.0-1.data', False),
    ('somepackage-1.0.0.dist-info', False),
    ('SOME_._PaCkAgE-0.data', True),
    ('foo-1!2+local.data', True),
    ('foo-1_2_local.data', True),
    ('.data', False),
])
def test_is_data_dir(name, expected):
    assert is_data_dir(name) is expected

@pytest.mark.parametrize('namelist,project,version,expected', [
    (
        [
            "foo.py",
            "foo-1.0.dist-info/WHEEL",
            "foo-1.0.dist-info/RECORD",
        ],
        "foo",
        "1.0",
        "foo-1.0.dist-info",
    ),
    (
        [
            "foo.py",
            "FOO-1.0.0.dist-info/WHEEL",
            "FOO-1.0.0.dist-info/RECORD",
        ],
        "foo",
        "1.0",
        "FOO-1.0.0.dist-info"
    ),
    (
        [
            "foo.py",
            "foo-1.dist-info/WHEEL",
            "foo-1.dist-info/RECORD",
        ],
        "foo",
        "1.0",
        "foo-1.dist-info"
    ),
    (
        [
            "foo.py",
            "FOO-1.0_1.dist-info/WHEEL",
            "FOO-1.0_1.dist-info/RECORD",
        ],
        "foo",
        "1.0.post1",
        "FOO-1.0_1.dist-info",
    ),
])
def test_find_dist_info_dir(namelist, project, version, expected):
    assert find_dist_info_dir(namelist, project, version) == expected

@pytest.mark.parametrize('namelist,project,version,msg', [
    (
        [
            "foo.py",
            "foo-1.0.dist/WHEEL",
        ],
        "foo",
        "1.0",
        'No .dist-info directory in wheel',
    ),
    (
        [
            "foo.py",
            "bar-1.0.dist-info/WHEEL",
        ],
        "foo",
        "1.0",
        "Project & version of wheel's .dist-info directory do not match wheel"
        " name: 'bar-1.0.dist-info'"
    ),
    (
        [
            "foo.py",
            "foo-2.0.dist-info/WHEEL",
        ],
        "foo",
        "1.0",
        "Project & version of wheel's .dist-info directory do not match wheel"
        " name: 'foo-2.0.dist-info'"
    ),
    (
        [
            "foo.py",
            "foo-1.0.dist-info/WHEEL",
            "bar-2.0.dist-info/RECORD",
        ],
        "foo",
        "1.0",
        'Wheel contains multiple .dist-info directories',
    ),
    (
        [
            "foo.py",
            "FOO-1.0.0.dist-info/WHEEL",
            "foo-1.dist-info/RECORD",
        ],
        "foo",
        "1.0",
        'Wheel contains multiple .dist-info directories',
    ),
    (
        ["foo.py", ".dist-info/WHEEL"],
        "foo",
        "1.0",
        'No .dist-info directory in wheel',
    ),
])
def test_find_dist_info_dir_error(namelist, project, version, msg):
    with pytest.raises(DistInfoError) as excinfo:
        find_dist_info_dir(namelist, project, version)
    assert str(excinfo.value) == msg

### TODO: Add more test cases for all functions!
