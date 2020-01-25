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
