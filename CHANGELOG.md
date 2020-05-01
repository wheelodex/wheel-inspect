v1.6.0 (2020-05-01)
-------------------
- Added an `inspect_dist_info_dir()` function for inspecting bare, unpacked
  `*.dist-info` directories
- Added a `DIST_INFO_SCHEMA` schema describing the return value of
  `inspect_dist_info_dir()`
- Renamed `SCHEMA` to `WHEEL_SCHEMA`; the value remains available under the
  old name for backwards compatibility
- The `wheel2json` command now accepts directory arguments and inspects them
  with `inspect_dist_info_dir()`


v1.5.0 (2020-04-21)
-------------------
- **Bugfix**: Now *actually* discard *all* empty keywords
- Split off the wheel filename processing code into its own package,
  [wheel-filename](https://github.com/jwodder/wheel-filename).  Wheel-Inspect
  currently re-exports `ParsedWheelFilename` and `parse_wheel_filename()` from
  this library in order to maintain API compatibility with earlier versions,
  but this may change in the future.
- Adjusted the schema to indicate that `.dist_info.metadata.description` may be
  `null`
- Binary extension modules and modules located in `*.data/{purelib,platlib}`
  are now included in `.derived.modules`


v1.4.1 (2020-03-12)
-------------------
- Drop support for Python 3.4
- Update `property-manager` dependency, thereby eliminating a
  DeprecationWarning


v1.4.0 (2020-01-25)
-------------------
- When splitting apart comma-separated keywords, trim whitespace and discard
  any keywords that are empty or all-whitespace
- Support Python 3.8


v1.3.0 (2019-05-09)
-------------------
- Upgraded `wheel_inspect.SCHEMA` from JSON Schema draft 4 to draft 7
- Don't require directory entries in wheels to be listed in `RECORD`


v1.2.1 (2019-04-20)
-------------------
- Include `pyproject.toml` in `MANIFEST.in`, thereby making it possible to
  build from sdist


v1.2.0 (2019-04-20)
-------------------
- `.derived.keywords` is now sorted and duplicate-free


v1.1.0 (2018-10-28)
-------------------
- `"buildver"` is now `None`/`null` instead of the empty string when there is
  no build tag in the wheel's filename
- Added a `parse_wheel_filename()` function for parsing a wheel filename into
  its components
- Validation of `RECORD` files is now done directly by `wheel-inspect` instead
  of with `distlib` in order to achieve more descriptive error messages


v1.0.0 (2018-10-12)
-------------------
Initial release

This project's code was previously part of
[Wheelodex](https://github.com/jwodder/wheelodex).
