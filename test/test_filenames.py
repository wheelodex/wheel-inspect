import pytest
from   wheel_inspect        import ParsedWheelFilename, parse_wheel_filename
from   wheel_inspect.errors import InvalidFilenameError

@pytest.mark.parametrize('filename,parsed', [
    (
        "astrocats-0.3.2-universal-none-any.whl",
        ParsedWheelFilename(
            project='astrocats',
            version='0.3.2',
            build=None,
            python_tags=['universal'],
            abi_tags=['none'],
            platform_tags=['any'],
        ),
    ),

    (
        "bencoder.pyx-1.1.2-pp226-pp226-win32.whl",
        ParsedWheelFilename(
            project='bencoder.pyx',
            version='1.1.2',
            build=None,
            python_tags=['pp226'],
            abi_tags=['pp226'],
            platform_tags=['win32'],
        ),
    ),

    (
        "brotlipy-0.1.2-pp27-none-macosx_10_10_x86_64.whl",
        ParsedWheelFilename(
            project='brotlipy',
            version='0.1.2',
            build=None,
            python_tags=['pp27'],
            abi_tags=['none'],
            platform_tags=['macosx_10_10_x86_64'],
        ),
    ),

    (
        "brotlipy-0.3.0-pp226-pp226u-macosx_10_10_x86_64.whl",
        ParsedWheelFilename(
            project='brotlipy',
            version='0.3.0',
            build=None,
            python_tags=['pp226'],
            abi_tags=['pp226u'],
            platform_tags=['macosx_10_10_x86_64'],
        ),
    ),

    (
        "carbonara_archinfo-7.7.9.14.post1-py2-none-any.whl",
        ParsedWheelFilename(
            project='carbonara_archinfo',
            version='7.7.9.14.post1',
            build=None,
            python_tags=['py2'],
            abi_tags=['none'],
            platform_tags=['any'],
        ),
    ),

    (
        "coremltools-0.3.0-py2.7-none-any.whl",
        ParsedWheelFilename(
            project='coremltools',
            version='0.3.0',
            build=None,
            python_tags=['py2', '7'],
            abi_tags=['none'],
            platform_tags=['any'],
        ),
    ),

    (
        "cvxopt-1.2.0-001-cp34-cp34m-macosx_10_6_intel.macosx_10_9_intel.macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64.whl",
        ParsedWheelFilename(
            project='cvxopt',
            version='1.2.0',
            build='001',
            python_tags=['cp34'],
            abi_tags=['cp34m'],
            platform_tags=[
                'macosx_10_6_intel',
                'macosx_10_9_intel',
                'macosx_10_9_x86_64',
                'macosx_10_10_intel',
                'macosx_10_10_x86_64',
            ],
        ),
    ),

    (
        "django_mbrowse-0.0.1-10-py2-none-any.whl",
        ParsedWheelFilename(
            project='django_mbrowse',
            version='0.0.1',
            build='10',
            python_tags=['py2'],
            abi_tags=['none'],
            platform_tags=['any'],
        ),
    ),

    (
        'efilter-1!1.2-py2-none-any.whl',
        ParsedWheelFilename(
            project='efilter',
            version='1!1.2',
            build=None,
            python_tags=['py2'],
            abi_tags=['none'],
            platform_tags=['any'],
        ),
    ),

    (
        "line.sep-0.2.0.dev1-py2.py3-none-any.whl",
        ParsedWheelFilename(
            project='line.sep',
            version='0.2.0.dev1',
            build=None,
            python_tags=['py2', 'py3'],
            abi_tags=['none'],
            platform_tags=['any'],
        ),
    ),

    (
        "mayan_edms-1.1.0-1502100955-py2-none-any.whl",
        ParsedWheelFilename(
            project='mayan_edms',
            version='1.1.0',
            build='1502100955',
            python_tags=['py2'],
            abi_tags=['none'],
            platform_tags=['any'],
        ),
    ),

    (
        "mxnet_model_server-1.0a5-20180816-py2.py3-none-any.whl",
        ParsedWheelFilename(
            project='mxnet_model_server',
            version='1.0a5',
            build='20180816',
            python_tags=['py2', 'py3'],
            abi_tags=['none'],
            platform_tags=['any'],
        ),
    ),

    (
        'pip-18.0-py2.py3-none-any.whl',
        ParsedWheelFilename(
            project='pip',
            version='18.0',
            build=None,
            python_tags=['py2', 'py3'],
            abi_tags=['none'],
            platform_tags=['any'],
        ),
    ),

    (
        "polarTransform-2-1.0.0-py3-none-any.whl",
        ParsedWheelFilename(
            project='polarTransform',
            version='2',
            build='1.0.0',
            python_tags=['py3'],
            abi_tags=['none'],
            platform_tags=['any'],
        ),
    ),

    (
        'psycopg2-2.7.5-cp37-cp37m-macosx_10_6_intel.macosx_10_9_intel.macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64.whl',
        ParsedWheelFilename(
            project='psycopg2',
            version='2.7.5',
            build=None,
            python_tags=['cp37'],
            abi_tags=['cp37m'],
            platform_tags=[
                'macosx_10_6_intel',
                'macosx_10_9_intel',
                'macosx_10_9_x86_64',
                'macosx_10_10_intel',
                'macosx_10_10_x86_64',
            ],
        ),
    ),

    (
        "pyinterval-1.0.0-0-cp27-none-win32.whl",
        ParsedWheelFilename(
            project='pyinterval',
            version='1.0.0',
            build='0',
            python_tags=['cp27'],
            abi_tags=['none'],
            platform_tags=['win32'],
        ),
    ),

    (
        'pypi_simple-0.1.0.dev1-py2.py3-none-any.whl',
        ParsedWheelFilename(
            project='pypi_simple',
            version='0.1.0.dev1',
            build=None,
            python_tags=['py2', 'py3'],
            abi_tags=['none'],
            platform_tags=['any'],
        ),
    ),

    (
        "PyQt3D-5.7.1-5.7.1-cp34.cp35.cp36-abi3-macosx_10_6_intel.whl",
        ParsedWheelFilename(
            project='PyQt3D',
            version='5.7.1',
            build='5.7.1',
            python_tags=['cp34', 'cp35', 'cp36'],
            abi_tags=['abi3'],
            platform_tags=['macosx_10_6_intel'],
        ),
    ),

    (
        'qypi-0.4.1-py3-none-any.whl',
        ParsedWheelFilename(
            project='qypi',
            version='0.4.1',
            build=None,
            python_tags=['py3'],
            abi_tags=['none'],
            platform_tags=['any'],
        ),
    ),

    (
        "SimpleSteem-1.1.9-3.0-none-any.whl",
        ParsedWheelFilename(
            project='SimpleSteem',
            version='1.1.9',
            build=None,
            python_tags=['3', '0'],
            abi_tags=['none'],
            platform_tags=['any'],
        ),
    ),

    (
        "simple_workflow-0.1.47-pypy-none-any.whl",
        ParsedWheelFilename(
            project='simple_workflow',
            version='0.1.47',
            build=None,
            python_tags=['pypy'],
            abi_tags=['none'],
            platform_tags=['any'],
        ),
    ),

    (
        "tables-3.4.2-3-cp27-cp27m-manylinux1_i686.whl",
        ParsedWheelFilename(
            project='tables',
            version='3.4.2',
            build='3',
            python_tags=['cp27'],
            abi_tags=['cp27m'],
            platform_tags=['manylinux1_i686'],
        ),
    ),
])
def test_parse_wheel_filename(filename, parsed):
    assert parse_wheel_filename(filename) == parsed

@pytest.mark.parametrize('filename', [
    "arq-0.3-py35+-none-any.whl",
    "azure_iothub_service_client-1.1.0.0-py2-win32.whl",
    "bgframework-0.4-py2,py3,pypy-none-any.whl",
    "buoyant-0.5.2--py2.py3-none-any.whl",
    "circbuf-0.1b1-py32, py33, py34-none-any.whl",
    "devtools-0.1-py35,py36-none-any.whl",
    "nupic-0.0.31-py2-none-macosx-10.9-intel.whl",
    "qcodes_-0.1.0-py3-none-any.whl",
])
def test_bad_filename(filename):
    with pytest.raises(InvalidFilenameError) as excinfo:
        parse_wheel_filename(filename)
    assert excinfo.value.filename == filename
    assert str(excinfo.value) == 'Invalid wheel filename: ' + repr(filename)
