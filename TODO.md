- Improve documentation:
    - Improve `README`/module docstring
        - Make "Python wheel files" link somewhere
    - Publicly document `Wheel`
    - Publicly document `ParsedWheelFilename`'s `__str__` and `tag_triples()`
      methods
- Publicly expose `Record`?
- Give `Record` a `dump()`/`dumps()` method?
- Give `Wheel` `entry_points`, `top_level`, etc. attributes that evaluate to
  `None` if the respective files aren't present
- Rename `Wheel.parsed_filename` to `filename`?
- `ParsedWheelFilename.__str__`: Ensure that all non-alphanumeric/period
  characters in attributes are converted to underscores before concatenating?
- Give `ParsedWheelFilename` attributes for accessing the leading numeric
  portion of `build` and the rest of `build`?
- Problem: PEP 427 says that `!` and `+` aren't allowed in the version
  component of wheel filenames, but `bdist_wheel` generates such wheels anyway,
  and the `wheel` devs seem to currently be erring on the side of allowing such
  characters in wheel filenames
    - Change `parse_wheel_filename()` to accept any non-hyphen sequence as a
      filename component, with validation of the components as a separate step
      (possibly triggerable with a `strict=True` argument to
      `parse_wheel_filename()`) ?

Inspecting Wheels
-----------------
- Parse `Description-Content-Type` into a structured `dict`?
- Should flat modules inside packages be discarded from `.derived.modules`?
- Divide `.derived.modules` into a list of packages and a list of flat modules
  (or otherwise somehow indicate which is which)?
- `extract_modules()`: Take compiled library files into account
    - Compare with <https://github.com/takluyver/wheeldex>
- Determine namespace packages other than those listed in
  `namespace_packages.txt`?  (cf. wheeldex?)
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
- Add a `.derived.signed` field?
- Add a `.derived.type_checked`(?) field for whether `py.typed` is present?
  (See PEP 561)
- Give `inspect_wheel()` and `wheel2json` an option for whether to keep long
  descriptions
- Give `inspect_wheel()` and `wheel2json` an option for using PEP 566's schema
  for METADATA
- Include `pbr.json` contents?
- Don't proceed with inspecting wheels that fail validation?
- Support salvaging as much as possible from malformed `RECORD`s?

Validating Wheels
-----------------
- Add a dedicated error for `*.dist-info` not matching the project & version in
  the wheel filename?
- Should `NullEntryError` be a subclass of `MalformedRecordError` even though
  it's not raised by `Record.load()`?
- Implement complete wheel validation logic, including checking METADATA and
  other `*.dist-info` files
    - Add an option for whether to bother checking `setuptools` files like
      `entry_points.txt` that aren't specified by a PEP (default: do check)
    - Add a command for validating a given wheel
