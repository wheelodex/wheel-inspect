import json
from pathlib import Path
from typing import Sequence
import click
from .inspecting import inspect_dist_info_dir, inspect_wheel


@click.command()
@click.option(
    "--verify-files/--no-verify-files",
    default=True,
    help=(
        "Verify the digests of files listed inside wheels' RECORDs"
        "  [default: --verify-files]"
    ),
)
@click.argument("paths", type=click.Path(exists=True, path_type=Path))
def main(paths: Sequence[Path], verify_files: bool) -> None:
    for p in paths:
        if p.is_dir():
            about = inspect_dist_info_dir(p)
        else:
            about = inspect_wheel(p, verify_files=verify_files)
        print(json.dumps(about, sort_keys=True, indent=4))


if __name__ == "__main__":
    main()
