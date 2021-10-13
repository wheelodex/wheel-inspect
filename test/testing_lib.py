import json
from pathlib import Path
from typing import Iterable
from _pytest.mark import ParameterSet
import pytest

DATA_DIR = Path(__file__).with_name("data")


def filecases(subdir: str, glob_pattern: str) -> Iterable[ParameterSet]:
    for p in sorted((DATA_DIR / subdir).glob(glob_pattern)):
        with p.with_suffix(".json").open() as fp:
            expected = json.load(fp)
        yield pytest.param(p, expected, id=p.name)
