.. image:: http://www.repostatus.org/badges/latest/active.svg
    :target: http://www.repostatus.org/#active
    :alt: Project Status: Active — The project has reached a stable, usable
          state and is being actively developed.

.. image:: https://travis-ci.org/jwodder/wheel-inspect.svg?branch=master
    :target: https://travis-ci.org/jwodder/wheel-inspect

.. image:: https://codecov.io/gh/jwodder/wheel-inspect/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/jwodder/wheel-inspect

.. image:: https://img.shields.io/pypi/pyversions/wheel-inspect.svg
    :target: https://pypi.org/project/wheel-inspect/

.. image:: https://img.shields.io/github/license/jwodder/wheel-inspect.svg
    :target: https://opensource.org/licenses/MIT
    :alt: MIT License

.. image:: https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg
    :target: https://saythanks.io/to/jwodder

`GitHub <https://github.com/jwodder/wheel-inspect>`_
| `PyPI <https://pypi.org/project/wheel-inspect/>`_
| `Issues <https://github.com/jwodder/wheel-inspect/issues>`_
| `Changelog <https://github.com/jwodder/wheel-inspect/blob/master/CHANGELOG.md>`_

``wheel-inspect`` examines Python wheel files & ``*.dist-info`` directories and
outputs various information about their contents as JSON-serializable objects.
It can be invoked in Python code as::

    from wheel_inspect import inspect_wheel

    output = inspect_wheel(path_to_wheel_file)

or from the command line with the ``wheel2json`` command.


Installation
============
``wheel-inspect`` requires Python 3.5 or higher.  Just use `pip
<https://pip.pypa.io>`_ for Python 3 (You have pip, right?) to install
``wheel-inspect`` and its dependencies::

    python3 -m pip install wheel-inspect


Example
=======

::

    $ wheel2json wheel_inspect-1.0.0.dev1-py3-none-any.whl
    {
        "abi": [
            "none"
        ],
        "arch": [
            "any"
        ],
        "buildver": null,
        "derived": {
            "dependencies": [
                "distlib",
                "headerparser",
                "packaging",
                "readme-renderer",
                "setuptools"
            ],
            "description_in_body": true,
            "description_in_headers": false,
            "keyword_separator": ",",
            "keywords": [
                "packages",
                "pypi",
                "wheel"
            ],
            "modules": [
                "wheel_inspect",
                "wheel_inspect.__main__",
                "wheel_inspect.inspect",
                "wheel_inspect.metadata",
                "wheel_inspect.schema",
                "wheel_inspect.util",
                "wheel_inspect.wheel_info"
            ],
            "readme_renders": true
        },
        "dist_info": {
            "entry_points": {
                "console_scripts": {
                    "wheel2json": {
                        "attr": "main",
                        "extras": [],
                        "module": "wheel_inspect.__main__"
                    }
                }
            },
            "metadata": {
                "author": "John Thorvald Wodder II",
                "author_email": "wheel-inspect@varonathe.org",
                "classifier": [
                    "Development Status :: 3 - Alpha",
                    "Programming Language :: Python :: 3 :: Only",
                    "Programming Language :: Python :: 3",
                    "Programming Language :: Python :: 3.5",
                    "Programming Language :: Python :: 3.6",
                    "Programming Language :: Python :: 3.7",
                    "Programming Language :: Python :: Implementation :: CPython",
                    "Programming Language :: Python :: Implementation :: PyPy",
                    "License :: OSI Approved :: MIT License",
                    "Intended Audience :: Developers",
                    "Topic :: Software Development :: Libraries :: Python Modules",
                    "Topic :: System :: Software Distribution"
                ],
                "description": {
                    "length": 1538
                },
                "home_page": "https://github.com/jwodder/wheel-inspect",
                "keywords": "packages,pypi,wheel",
                "license": "MIT",
                "metadata_version": "2.1",
                "name": "wheel-inspect",
                "platform": [],
                "requires_dist": [
                    {
                        "extras": [],
                        "marker": null,
                        "name": "distlib",
                        "specifier": "~=0.2.7",
                        "url": null
                    },
                    {
                        "extras": [],
                        "marker": null,
                        "name": "headerparser",
                        "specifier": "~=0.2.0",
                        "url": null
                    },
                    {
                        "extras": [],
                        "marker": null,
                        "name": "packaging",
                        "specifier": ">=17.1",
                        "url": null
                    },
                    {
                        "extras": [],
                        "marker": null,
                        "name": "readme-renderer",
                        "specifier": "~=21.0",
                        "url": null
                    },
                    {
                        "extras": [],
                        "marker": null,
                        "name": "setuptools",
                        "specifier": ">=36",
                        "url": null
                    }
                ],
                "requires_python": "~=3.5",
                "summary": "Extract information from wheels",
                "version": "1.0.0.dev1"
            },
            "record": [
                {
                    "digests": {
                        "sha256": "EL9q_wQOJRlJL3LkKscASTrhXgXgVLfeugZz66MFeV8"
                    },
                    "path": "wheel_inspect/__init__.py",
                    "size": 440
                },
                {
                    "digests": {
                        "sha256": "3_DrJ4Tr-ie5TCQtmmTnS82eHTMmVDY1mOeSP_hJ_Ho"
                    },
                    "path": "wheel_inspect/__main__.py",
                    "size": 247
                },
                {
                    "digests": {
                        "sha256": "LCgjTkHaGxyzSKeY_pEDSWQFNQi7PRby6lh6H0OSVAQ"
                    },
                    "path": "wheel_inspect/inspect.py",
                    "size": 4816
                },
                {
                    "digests": {
                        "sha256": "3u83eQ0RBdR-AEOxqsPyMkc663G2Un9Hd6tqhO2eu6k"
                    },
                    "path": "wheel_inspect/metadata.py",
                    "size": 1946
                },
                {
                    "digests": {
                        "sha256": "8VOeroNaM34lIqdjnCiaCwtNEVwi_wFDTtYaL7dEXDQ"
                    },
                    "path": "wheel_inspect/schema.py",
                    "size": 12158
                },
                {
                    "digests": {
                        "sha256": "iaxC3qenCrPMRjrqdTwj1Hfy-OPo-y-WVLaPWEDeSFs"
                    },
                    "path": "wheel_inspect/util.py",
                    "size": 1352
                },
                {
                    "digests": {
                        "sha256": "wNTKsMw_TVe3RbIpj8tjwRE0Q_rUeoRUF66KKpqBp2c"
                    },
                    "path": "wheel_inspect/wheel_info.py",
                    "size": 1010
                },
                {
                    "digests": {
                        "sha256": "-X7Ry_-tNPLAGkZasQc2KOBW_Ohnx52rgDZfo8cxw10"
                    },
                    "path": "wheel_inspect-1.0.0.dev1.dist-info/LICENSE",
                    "size": 1095
                },
                {
                    "digests": {
                        "sha256": "SbhMBq15toKwrurqS0Xmt--MPsWRvKTjtx9ya4tTed8"
                    },
                    "path": "wheel_inspect-1.0.0.dev1.dist-info/METADATA",
                    "size": 2692
                },
                {
                    "digests": {
                        "sha256": "-ZFxwj8mZJPIVcZGLrsQ8UGRcxVAOExzPLVBGR7u7bE"
                    },
                    "path": "wheel_inspect-1.0.0.dev1.dist-info/WHEEL",
                    "size": 92
                },
                {
                    "digests": {
                        "sha256": "fqJPsljFaWRzPdYMreNAf0zg8GSQE0Tgh8_XOzL85lo"
                    },
                    "path": "wheel_inspect-1.0.0.dev1.dist-info/entry_points.txt",
                    "size": 60
                },
                {
                    "digests": {
                        "sha256": "Cz2n0fdOaOfDcl0g6x4t_DEWzWZYYRcFASrgxW0v_WE"
                    },
                    "path": "wheel_inspect-1.0.0.dev1.dist-info/top_level.txt",
                    "size": 14
                },
                {
                    "digests": {},
                    "path": "wheel_inspect-1.0.0.dev1.dist-info/RECORD",
                    "size": null
                }
            ],
            "top_level": [
                "wheel_inspect"
            ],
            "wheel": {
                "generator": "bdist_wheel (0.32.1)",
                "root_is_purelib": true,
                "tag": [
                    "py3-none-any"
                ],
                "wheel_version": "1.0"
            }
        },
        "file": {
            "digests": {
                "md5": "fc6dcdac9f850435e41167f48e3862f4",
                "sha256": "69733fa29a205ecfee322961defd15dc42880873869db6a742edf26d6d6d4832"
            },
            "size": 10208
        },
        "filename": "wheel_inspect-1.0.0.dev1-py3-none-any.whl",
        "project": "wheel_inspect",
        "pyver": [
            "py3"
        ],
        "valid": true,
        "version": "1.0.0.dev1"
    }


API
===

``wheel_inspect.DIST_INFO_SCHEMA``
   A `JSON Schema <http://json-schema.org>`_ for the structure returned by
   ``inspect_dist_info_dir()``.  It is the same as ``WHEEL_SCHEMA``, but
   without the ``"filename"``, ``"project"``, ``"version"``, ``"buildver"``,
   ``"pyver"``, ``"abi"``, ``"arch"``, and ``"file"`` keys.

``wheel_inspect.WHEEL_SCHEMA``
   A `JSON Schema <http://json-schema.org>`_ for the structure returned by
   ``inspect_wheel()``.  This value was previously exported under the name
   "``SCHEMA``"; the old name continues to be available for backwards
   compatibility, but it will go away in the future and should not be used in
   new code.

``wheel_inspect.inspect_dist_info_dir(dirpath)``
   Treat ``dirpath`` as a ``*.dist-info`` directory and inspect just it & its
   contents.  The structure of the return value is described by
   ``DIST_INFO_SCHEMA``.

``wheel_inspect.inspect_wheel(path)``
   Inspect the wheel file at the given ``path``.  The structure of the return
   value is described by ``WHEEL_SCHEMA``.

Previous versions of ``wheel-inspect`` provided a ``parse_wheel_filename()``
function.  As of version 1.5.0, that feature has been split off into its own
package, `wheel-filename <https://github.com/jwodder/wheel-filename>`_.
``wheel-inspect`` continues to re-export this function in order to maintain API
compatibility with earlier versions, but this will change in the future.  Code
that imports ``parse_wheel_filename()`` from ``wheel-inspect`` should be
updated to use ``wheel-filename`` instead.


Command
=======

::

    wheel2json [<path> ...]

``wheel-inspect`` provides a ``wheel2json`` command (also accessible as
``python -m wheel_inspect``) that can be used to inspect wheels and
``*.dist-info`` directories from the command line.  Each path passed to the
command is inspected separately (treated as a ``*.dist-info`` directory if it
is a directory, treated as a wheel file otherwise), and the resulting data is
output as a pretty-printed JSON object.  (Note that this results in a stream of
JSON objects with no separation when multiple paths are given.)
