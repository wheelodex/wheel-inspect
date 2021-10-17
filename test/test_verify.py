from pathlib import Path
from typing import Any
import pytest
from testing_lib import filecases
from wheel_inspect.classes import WheelFile
from wheel_inspect.errors import WheelError
from wheel_inspect.util import for_json


@pytest.mark.parametrize("whlfile,expected", filecases("bad-wheels", "*.whl"))
def test_verify_bad_wheels(whlfile: Path, expected: Any) -> None:
    with WheelFile.from_path(whlfile, strict=False) as whl:
        with pytest.raises(WheelError) as excinfo:
            whl.verify()
        assert for_json(excinfo.value) == expected
