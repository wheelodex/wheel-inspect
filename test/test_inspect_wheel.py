import json
from operator import attrgetter
from pathlib import Path
from typing import Any
from zipfile import ZipFile
from jsonschema import validate
import pytest
from testing_lib import filecases
from wheel_inspect import (
    WHEEL_SCHEMA,
    UnpackedWheelDir,
    inspect,
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
    validate(inspection, WHEEL_SCHEMA)


@pytest.mark.parametrize("whlfile,expected", filecases("wheels", "*.whl"))
def test_inspect_unpacked_wheel_dir(
    whlfile: Path, expected: Any, tmp_path: Path
) -> None:
    with ZipFile(whlfile) as zf:
        zf.extractall(tmp_path)
    with UnpackedWheelDir.from_path(
        tmp_path, wheel_name=whlfile.name, strict=False
    ) as uwd:
        inspection = inspect(uwd)
    assert inspection == expected
    validate(inspection, WHEEL_SCHEMA)
