|repostatus| |ci-status| |coverage| |pyversions| |license|

.. |repostatus| image:: https://www.repostatus.org/badges/latest/active.svg
    :target: https://www.repostatus.org/#active
    :alt: Project Status: Active — The project has reached a stable, usable
          state and is being actively developed.

.. |ci-status| image:: https://github.com/wheelodex/wheel-inspect/actions/workflows/test.yml/badge.svg
    :target: https://github.com/wheelodex/wheel-inspect/actions/workflows/test.yml
    :alt: CI Status

.. |coverage| image:: https://codecov.io/gh/wheelodex/wheel-inspect/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/wheelodex/wheel-inspect

.. |pyversions| image:: https://img.shields.io/pypi/pyversions/wheel-inspect.svg
    :target: https://pypi.org/project/wheel-inspect/

.. |license| image:: https://img.shields.io/github/license/wheelodex/wheel-inspect.svg
    :target: https://opensource.org/licenses/MIT
    :alt: MIT License

`GitHub <https://github.com/wheelodex/wheel-inspect>`_
| `PyPI <https://pypi.org/project/wheel-inspect/>`_
| `Issues <https://github.com/wheelodex/wheel-inspect/issues>`_
| `Changelog <https://github.com/wheelodex/wheel-inspect/blob/master/CHANGELOG.md>`_

``wheel-inspect`` examines Python wheel files & ``*.dist-info`` directories and
outputs various information about their contents as JSON-serializable objects.
It can be invoked in Python code as::

    from wheel_inspect import inspect_wheel

    output = inspect_wheel(path_to_wheel_file)

or from the command line with the ``wheel2json`` command.


Installation
============
``wheel-inspect`` requires Python 3.10 or higher.  Just use `pip
<https://pip.pypa.io>`_ for Python 3 (You have pip, right?) to install
``wheel-inspect`` and its dependencies::

    python3 -m pip install wheel-inspect


Example
=======

::

    $ wheel2json wheel_inspect-2.0.0.dev1-py3-none-any.whl
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
                "attrs",
                "entry-points-txt",
                "headerparser",
                "packaging",
                "readme-renderer",
                "wheel-filename"
            ],
            "description_in_body": true,
            "description_in_headers": false,
            "keyword_separator": ",",
            "keywords": [
                "*.dist-info",
                "dist-info",
                "package metadata",
                "packages",
                "pep427",
                "wheel"
            ],
            "modules": [
                "wheel_inspect",
                "wheel_inspect.__main__",
                "wheel_inspect.classes",
                "wheel_inspect.errors",
                "wheel_inspect.inspecting",
                "wheel_inspect.metadata",
                "wheel_inspect.record",
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
                "author_email": "John Thorvald Wodder II <wheel-inspect@varonathe.org>",
                "classifier": [
                    "Intended Audience :: Developers",
                    "Programming Language :: Python :: 3",
                    "Programming Language :: Python :: 3 :: Only",
                    "Programming Language :: Python :: 3.10",
                    "Programming Language :: Python :: 3.11",
                    "Programming Language :: Python :: 3.12",
                    "Programming Language :: Python :: 3.13",
                    "Programming Language :: Python :: 3.14",
                    "Programming Language :: Python :: Implementation :: CPython",
                    "Programming Language :: Python :: Implementation :: PyPy",
                    "Topic :: Software Development :: Libraries :: Python Modules",
                    "Topic :: System :: Software Distribution"
                ],
                "description": {
                    "length": 11863
                },
                "description_content_type": "text/x-rst",
                "keywords": "*.dist-info,dist-info,package metadata,packages,pep427,wheel",
                "license_expression": [
                    "MIT"
                ],
                "license_file": [
                    "LICENSE"
                ],
                "metadata_version": "2.4",
                "name": "wheel-inspect",
                "project_url": [
                    {
                        "label": "Source Code",
                        "url": "https://github.com/wheelodex/wheel-inspect"
                    },
                    {
                        "label": "Bug Tracker",
                        "url": "https://github.com/wheelodex/wheel-inspect/issues"
                    }
                ],
                "requires_dist": [
                    {
                        "extras": [],
                        "marker": null,
                        "name": "attrs",
                        "specifier": ">=18.1",
                        "url": null
                    },
                    {
                        "extras": [],
                        "marker": null,
                        "name": "entry-points-txt",
                        "specifier": "~=0.2",
                        "url": null
                    },
                    {
                        "extras": [],
                        "marker": null,
                        "name": "headerparser",
                        "specifier": "<0.6,>=0.4",
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
                        "specifier": ">=24.0",
                        "url": null
                    },
                    {
                        "extras": [],
                        "marker": null,
                        "name": "wheel-filename",
                        "specifier": "~=2.0",
                        "url": null
                    }
                ],
                "requires_python": "~=3.10",
                "summary": "Extract information from wheels",
                "version": "2.0.0.dev1"
            },
            "record": [
                {
                    "digests": {
                        "sha256": "eBA9pqLw20kl1d0I2E6yG8MJCxREtUXhWgiHcAm-oEc"
                    },
                    "path": "wheel_inspect/__init__.py",
                    "size": 875
                },
                {
                    "digests": {
                        "sha256": "m6zOH_MZevT5WzFdCI2HZTlhBOgyswWKM6FfP7wY4mA"
                    },
                    "path": "wheel_inspect/__main__.py",
                    "size": 376
                },
                {
                    "digests": {
                        "sha256": "oHVtmRzOPoGsu18gEQMO_CAncXXoFaW8hOGveGvrIuM"
                    },
                    "path": "wheel_inspect/classes.py",
                    "size": 6945
                },
                {
                    "digests": {
                        "sha256": "ZiGZPfNSL5vMxLMI5ZrkHLPrWJ9lwJVZt-z4c-lY0Ho"
                    },
                    "path": "wheel_inspect/errors.py",
                    "size": 9377
                },
                {
                    "digests": {
                        "sha256": "-F64pYZTI18Y_wxCvhc6T4YpQGDMenBDQtyZ8a_vpH8"
                    },
                    "path": "wheel_inspect/inspecting.py",
                    "size": 7546
                },
                {
                    "digests": {
                        "sha256": "xZtruc32eG9srzTZUeG0NYPHLf-71wyZNQYIeOajuHU"
                    },
                    "path": "wheel_inspect/metadata.py",
                    "size": 1884
                },
                {
                    "digests": {
                        "sha256": "Oarhze09xkqriiZCD0cmCybBTMbJ1iswKzt9TgSMATQ"
                    },
                    "path": "wheel_inspect/record.py",
                    "size": 3355
                },
                {
                    "digests": {
                        "sha256": "jYJKlNJPX3wGjaZQsg8OGDY4skctyuMMnJTGc5auwgU"
                    },
                    "path": "wheel_inspect/schema.py",
                    "size": 13466
                },
                {
                    "digests": {
                        "sha256": "RIqnwt1EVYSMTilWhT1DhU80Kq3GPVC_p_P-ryu0PpU"
                    },
                    "path": "wheel_inspect/util.py",
                    "size": 4652
                },
                {
                    "digests": {
                        "sha256": "OrGvWKuimWFdYecDhi87ee-OaUYVtdUxYIGQoRNzLUo"
                    },
                    "path": "wheel_inspect/wheel_info.py",
                    "size": 2353
                },
                {
                    "digests": {
                        "sha256": "3nX5mcnZcAqdbUiJ0XZbUQeIslSmVDWzc6p2JFXO4X8"
                    },
                    "path": "wheel_inspect-2.0.0.dev1.dist-info/METADATA",
                    "size": 13235
                },
                {
                    "digests": {
                        "sha256": "WLgqFyCfm_KASv4WHyYy0P3pM_m7J5L9k2skdKLirC8"
                    },
                    "path": "wheel_inspect-2.0.0.dev1.dist-info/WHEEL",
                    "size": 87
                },
                {
                    "digests": {
                        "sha256": "foQEXXq6je87QypdIpwLWvQZpZYHxumdba5GC5Wicbo"
                    },
                    "path": "wheel_inspect-2.0.0.dev1.dist-info/entry_points.txt",
                    "size": 59
                },
                {
                    "digests": {
                        "sha256": "ChyQxNLg7572tAsQz6UPE2M8WloSDwtw4kAYPFkSfeQ"
                    },
                    "path": "wheel_inspect-2.0.0.dev1.dist-info/licenses/LICENSE",
                    "size": 1095
                },
                {
                    "digests": {},
                    "path": "wheel_inspect-2.0.0.dev1.dist-info/RECORD",
                    "size": null
                }
            ],
            "wheel": {
                "generator": [
                    "hatchling 1.28.0"
                ],
                "root_is_purelib": true,
                "tag": [
                    "py3-none-any"
                ],
                "wheel_version": "1.0"
            }
        },
        "file": {
            "digests": {
                "md5": "7778ef6a69d3ccc96ec2030d74e58821",
                "sha256": "23bb30e72eb33400819f41961bdfeb33f3d8fc0f59394e59e5ccd4b84d859b48"
            },
            "size": 19924
        },
        "filename": "wheel_inspect-2.0.0.dev1-py3-none-any.whl",
        "project": "wheel_inspect",
        "pyver": [
            "py3"
        ],
        "valid": true,
        "version": "2.0.0.dev1"
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
