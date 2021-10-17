.. index:: wheel2json (command)

Command-Line Program
====================

::

    wheel2json [<option>] [<path> ...]

``wheel-inspect`` provides a :command:`wheel2json` command (also accessible as
``python -m wheel_inspect``) that can be used to inspect wheels and
:file:`*.dist-info` directories from the command line.  Each path passed to the
command is inspected separately (treated as a :file:`*.dist-info` directory if
it is a directory, treated as a wheel file otherwise), and the resulting data
is output as a pretty-printed JSON object.  (Note that this results in a stream
of JSON objects with no separation when multiple paths are given.)

Options
-------

.. program:: wheel2json

.. option:: --digest-files

    Verify the digests of files listed inside wheels' :file:`RECORD`\s.  This
    is the default.

.. option:: --no-digest-files

    Do not verify file digests
