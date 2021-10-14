from pathlib import Path
from typing import Any
import pytest
from testing_lib import filecases
from wheel_inspect.classes import WheelFile
from wheel_inspect.errors import WheelValidationError


@pytest.mark.parametrize("whlfile,expected", filecases("bad-wheels", "*.whl"))
def test_verify_bad_wheels(whlfile: Path, expected: Any) -> None:
    with WheelFile.from_path(whlfile) as whl:
        with pytest.raises(WheelValidationError) as excinfo:
            whl.verify_record()
        assert type(excinfo.value).__name__ == expected["type"]
        assert str(excinfo.value) == expected["str"]
