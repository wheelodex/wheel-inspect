from copy import deepcopy
from typing import Any, Dict

#: A `JSON Schema <http://json-schema.org>`_ for the structure returned by
#: `inspect_dist_info_dir()` and by `inspect()` when called on a `DistInfoDir`.
#: It is the same as `WHEEL_SCHEMA`, but without the ``"filename"``,
#: ``"project"``, ``"version"``, ``"buildver"``, ``"pyver"``, ``"abi"``,
#: ``"arch"``, and ``"file"`` keys.
DIST_INFO_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["valid", "dist_info", "derived"],
    "additionalProperties": False,
    "properties": {
        "valid": {
            "type": "boolean",
            "description": "Whether the wheel is well-formed with an accurate RECORD",
        },
        "validation_error": {
            "type": "object",
            "description": "If the wheel is invalid, this field contains information on the `WheelValidationError` raised.",
            "required": ["type", "str"],
            "additionalProperties": False,
            "properties": {
                "type": {
                    "type": "string",
                    "description": "The name of the type of exception raised",
                },
                "str": {
                    "type": "string",
                    "description": "The exception's error message",
                },
            },
        },
        "dist_info": {
            "type": "object",
            "description": "JSONifications of files from the wheel's .dist-info directory",
            "additionalProperties": False,
            "properties": {
                "metadata": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "properties": {
                        "metadata_version": {"type": "string"},
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                        "summary": {"type": ["null", "string"]},
                        "description": {
                            "oneOf": [
                                {"type": "null"},
                                {
                                    "type": "object",
                                    "requires": ["length"],
                                    "additionalProperties": False,
                                    "properties": {"length": {"type": "integer"}},
                                },
                            ]
                        },
                        "requires_dist": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": [
                                    "name",
                                    "url",
                                    "extras",
                                    "specifier",
                                    "marker",
                                ],
                                "additionalProperties": False,
                                "properties": {
                                    "name": {"type": "string"},
                                    "url": {"type": ["null", "string"]},
                                    "extras": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "specifier": {"type": "string"},
                                    "marker": {"type": ["null", "string"]},
                                },
                            },
                        },
                        "project_url": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "requires": ["label", "url"],
                                "additionalProperties": False,
                                "properties": {
                                    "label": {"type": ["null", "string"]},
                                    "url": {"type": "string"},
                                },
                            },
                        },
                        "requires_python": {"type": "string"},
                        "author": {"type": ["null", "string"]},
                        "author_email": {"type": ["null", "string"]},
                        "download_url": {"type": ["null", "string"]},
                        "home_page": {"type": ["null", "string"]},
                        "license": {"type": ["null", "string"]},
                        "maintainer": {"type": ["null", "string"]},
                        "maintainer_email": {"type": ["null", "string"]},
                        "keywords": {"type": ["null", "string"]},
                        "description_content_type": {"type": ["null", "string"]},
                    },
                },
                "record": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["path", "digest", "size"],
                        "additionalProperties": False,
                        "properties": {
                            "path": {"type": "string"},
                            "digest": {
                                "type": ["null", "object"],
                                "additionalProperties": False,
                                "required": ["algorithm", "digest"],
                                "properties": {
                                    "algorithm": {"type": "string"},
                                    "digest": {
                                        "type": "string",
                                        "pattern": "^[-_0-9A-Za-z]+$",
                                    },
                                },
                            },
                            "size": {"type": ["null", "integer"]},
                        },
                    },
                },
                "wheel": {
                    "type": "object",
                    "required": [
                        "wheel_version",
                        "generator",
                        "root_is_purelib",
                        "tag",
                    ],
                    "additionalProperties": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "properties": {
                        "wheel_version": {"type": "string"},
                        "generator": {"type": "string"},
                        "root_is_purelib": {"type": "boolean"},
                        "tag": {"type": "array", "items": {"type": "string"}},
                        "build": {"type": "string"},
                        "BODY": {"type": "string"},
                    },
                },
                "dependency_links": {"type": "array", "items": {"type": "string"}},
                "entry_points": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "required": ["module", "attr", "extras"],
                            "additionalProperties": False,
                            "properties": {
                                "module": {"type": "string"},
                                "attr": {"type": ["null", "string"]},
                                "extras": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                        },
                    },
                },
                "namespace_packages": {"type": "array", "items": {"type": "string"}},
                "top_level": {"type": "array", "items": {"type": "string"}},
                "zip_safe": {"type": "boolean"},
            },
        },
        "derived": {
            "type": "object",
            "description": "Information derived from `dist_info`",
            "required": [
                "readme_renders",
                "description_in_body",
                "description_in_headers",
                "keywords",
                "keyword_separator",
                "dependencies",
                "modules",
            ],
            "additionalProperties": False,
            "properties": {
                "readme_renders": {
                    "type": ["null", "boolean"],
                    "description": "Whether the description's markup can be rendered successfully on PyPI.  A value of `null` indicates that there is no description.",
                },
                "description_in_body": {
                    "type": "boolean",
                    "description": "Whether the description is present as the message body in the METADATA file",
                },
                "description_in_headers": {
                    "type": "boolean",
                    "description": "Whether the description is present as a header field in the METADATA file",
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "uniqueItems": True,
                    "description": "The wheel's keywords string, split on what appears to be the appropriate separator",
                },
                "keyword_separator": {
                    "enum": [" ", ",", None],
                    "description": "The apparent appropriate separator for the wheel's keywords string.  A value of `null` indicates that the keywords string is undefined.",
                },
                "dependencies": {
                    "type": "array",
                    "items": {"type": "string"},
                    "uniqueItems": True,
                    "description": "The names of all of the projects listed in the wheel's Requires-Dist",
                },
                "modules": {
                    "type": "array",
                    "items": {"type": "string"},
                    "uniqueItems": True,
                    "description": "A list of Python modules installed by the wheel",
                },
            },
        },
    },
}

#: A `JSON Schema <http://json-schema.org>`_ for the structure returned by
#: `inspect_wheel()` and by `inspect()` when called on a `WheelFile`.
WHEEL_SCHEMA: Dict[str, Any] = deepcopy(DIST_INFO_SCHEMA)

WHEEL_SCHEMA["required"].extend(
    [
        "filename",
        "project",
        "version",
        "buildver",
        "pyver",
        "abi",
        "arch",
        "file",
    ]
)

WHEEL_SCHEMA["properties"].update(
    {
        "filename": {"type": "string", "description": "The filename of the wheel"},
        "project": {
            "type": "string",
            "description": "The name of the wheel's project as extracted from the filename",
        },
        "version": {
            "type": "string",
            "description": "The wheel's project version as extracted from the filename",
        },
        "buildver": {
            "type": ["string", "null"],
            "description": "The wheel's build tag as extracted from the filename; `null` if there is no build tag",
        },
        "pyver": {
            "type": "array",
            "items": {"type": "string"},
            "description": "A list of Python versions with which the wheel is compatible as extracted from the filename",
        },
        "abi": {
            "type": "array",
            "items": {"type": "string"},
            "description": "A list of ABIs with which the wheel is compatible as extracted from the filename",
        },
        "arch": {
            "type": "array",
            "items": {"type": "string"},
            "description": "A list of architectures with which the wheel is compatible as extracted from the filename",
        },
        "file": {
            "type": "object",
            "required": ["size", "digests"],
            "additionalProperties": False,
            "properties": {
                "size": {"type": "integer"},
                "digests": {
                    "type": "object",
                    "required": ["md5", "sha256"],
                    "additionalProperties": False,
                    "properties": {
                        "md5": {"type": "string", "pattern": "^[0-9A-Fa-f]{32}$"},
                        "sha256": {"type": "string", "pattern": "^[0-9A-Fa-f]{64}$"},
                    },
                },
            },
        },
    }
)
