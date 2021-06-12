import json
from pathlib import Path
import pytest

DATA_DIR = Path(__file__).with_name("data")


def filecases(subdir, glob_pattern):
    for p in sorted((DATA_DIR / subdir).glob(glob_pattern)):
        with p.with_suffix(".json").open() as fp:
            expected = json.load(fp)
        yield pytest.param(p, expected, id=p.name)
