import json
from operator import attrgetter
from pathlib import Path
from typing import Any
from jsonschema import validate
import pytest
from testing_lib import filecases
from wheel_inspect import (
    DIST_INFO_SCHEMA,
    WHEEL_SCHEMA,
    inspect_dist_info_dir,
    inspect_wheel,
)


@pytest.mark.parametrize("whlfile,expected", filecases("wheels", "*.whl"))
def test_inspect_wheel(whlfile: Path, expected: Any) -> None:
    inspection = inspect_wheel(whlfile)
    assert inspection == expected
    validate(inspection, WHEEL_SCHEMA)


@pytest.mark.parametrize(
    "didir",
    [
        p
        for p in (Path(__file__).with_name("data") / "dist-infos").iterdir()
        if p.is_dir()
    ],
    ids=attrgetter("name"),
)
def test_inspect_dist_info_dir(didir: Path) -> None:
    with open(str(didir) + ".json") as fp:
        expected = json.load(fp)
    inspection = inspect_dist_info_dir(didir)
    assert inspection == expected
    validate(inspection, DIST_INFO_SCHEMA)
