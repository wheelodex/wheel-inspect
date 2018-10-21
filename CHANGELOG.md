v1.1.0 (in development)
-----------------------
- `"buildver"` is now `None`/`null` instead of the empty string when there is
  no build tag in the wheel's filename
- Added a `parse_wheel_filename()` function for parsing a wheel filename into
  its components
- Validation of `RECORD` files is now done by `wheel-inspect` instead of
  `distlib` for more descriptive error messages

v1.0.0 (2018-10-12)
-------------------
Initial release

This project's code was previously part of
[Wheelodex](https://github.com/jwodder/wheelodex).
