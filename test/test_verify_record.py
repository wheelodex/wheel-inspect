import pytest
from testing_lib import filecases
from wheel_inspect.classes import WheelFile
from wheel_inspect.errors import WheelValidationError
from wheel_inspect.inspecting import verify_record


@pytest.mark.parametrize("whlfile,expected", filecases("bad-wheels", "*.whl"))
def test_verify_bad_wheels(whlfile, expected):
    with WheelFile(whlfile) as whl:
        with pytest.raises(WheelValidationError) as excinfo:
            verify_record(whl, whl.get_record())
        assert type(excinfo.value).__name__ == expected["type"]
        assert str(excinfo.value) == expected["str"]
