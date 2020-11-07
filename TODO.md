- Improve documentation:
    - Improve `README`/module docstring
        - Make "Python wheel files" link somewhere
    - Publicly document `WheelFile`
- Publicly expose `Record`?
- Give `Record` a `dump()`/`dumps()` method?
- Give `DistInfoProvider` methods for getting & parsing `entry_points.txt`,
  `top_level.txt`, etc.?
- Rename `WheelFile.parsed_filename` to `filename`?
- Add `--strict` and `inspect_wheel(..., strict: bool)` options for raising
  errors on wheel validation failures
- Add an option for disabling hash checking so that `wheelodex` can speed up
  analysis

Inspecting Wheels
-----------------
- Parse `Description-Content-Type` into a structured `dict`?
- Should flat modules inside packages be discarded from `.derived.modules`?
- Divide `.derived.modules` into a list of packages and a list of flat modules
  (or otherwise somehow indicate which is which)?
- Determine namespace packages other than those listed in
  `namespace_packages.txt`?  (cf. <https://github.com/takluyver/wheeldex>?)
- Include the results of testing manylinux1 wheels with `auditwheel`?
- Should (rarely used) fields similar to `Requires-Dist` be parsed into
  structured `dict`s?
    - `Obsoletes` - no longer supposed to exist?
    - `Obsoletes-Dist` - same format as `Requires-Dist`?
    - `Provides` - no longer supposed to exist?
    - `Provides-Dist` - same as `Requires-Dist` but with a single version
      number instead of a version specifier?
    - `Requires` - no longer supposed to exist?
    - `Requires-External` - same as `Requires-Dist` but with looser version
      string requirements?
- Move `.derived.readme_renders` to inside the
  `.dist_info.metadata.description` object?
    - Do likewise for the `.derived.description_in_*` fields?
- Add a `.derived.type_checked`(?) field for whether `py.typed` is present?
  (See PEP 561)
- Give `inspect_wheel()` and `wheel2json` an option for whether to keep long
  descriptions
- Give `inspect_wheel()` and `wheel2json` an option for using PEP 566's schema
  for METADATA
- Don't proceed with inspecting wheels that fail validation?
- Support salvaging as much as possible from malformed `RECORD`s?

Validating Wheels
-----------------
- Should `NullEntryError` be a subclass of `MalformedRecordError` even though
  it's not raised by `Record.load()`?
- Implement complete wheel validation logic, including checking METADATA and
  other `*.dist-info` files
    - Add an option for whether to bother checking `setuptools` files like
      `entry_points.txt` that aren't specified by a PEP (default: do check)
    - Add a command for validating a given wheel
