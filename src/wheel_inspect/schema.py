from typing import Any, Dict

#: A `JSON Schema <http://json-schema.org>`_ for the structure returned by
#: `~wheel_inspect.inspect()`, `~wheel_inspect.inspect_wheel()`, and
#: `~wheel_inspect.inspect_dist_info_dir()`.
WHEEL_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["valid", "dist_info", "derived", "wheel_name"],
    "additionalProperties": False,
    "properties": {
        "valid": {
            "type": "boolean",
            "description": "Whether the wheel is well-formed with an accurate RECORD",
        },
        "validation_error": {
            "type": "object",
            "description": "If the wheel is invalid, this field contains information on the `WheelError` raised.",
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
                    "type": "object",
                    "additionalProperties": False,
                    "patternProperties": {
                        "^([^\0/]+)(/[^\0/]+)*/?$": {
                            "type": ["null", "object"],
                            "additionalProperties": False,
                            "required": ["algorithm", "digest", "size"],
                            "properties": {
                                "algorithm": {"type": "string"},
                                "digest": {
                                    "type": "string",
                                    "pattern": "^[-_0-9A-Za-z]+$",
                                },
                                "size": {"type": "integer", "minimum": 0},
                            },
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
        "wheel_name": {
            "description": "Data obtained from the wheel's filename.  This is `null` if the file's name is unknown.",
            "type": ["null", "object"],
            "required": [
                "name",
                "project",
                "version",
                "build",
                "python_tags",
                "abi_tags",
                "platform_tags",
            ],
            "additionalProperties": False,
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The base filename of the wheel",
                },
                "project": {
                    "type": "string",
                    "description": "The name of the wheel's project as extracted from the filename",
                },
                "version": {
                    "type": "string",
                    "description": "The wheel's project version as extracted from the filename",
                },
                "build": {
                    "type": ["string", "null"],
                    "description": "The wheel's build tag as extracted from the filename; `null` if there is no build tag",
                },
                "python_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of Python versions with which the wheel is compatible as extracted from the filename",
                },
                "abi_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of ABIs with which the wheel is compatible as extracted from the filename",
                },
                "platform_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of platforms with which the wheel is compatible as extracted from the filename",
                },
            },
        },
    },
}
