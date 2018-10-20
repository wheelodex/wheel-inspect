import json
from   operator             import attrgetter
from   pathlib              import Path
import pytest
from   wheel_inspect        import Wheel
from   wheel_inspect.errors import WheelValidationError

@pytest.mark.parametrize('whlfile', [
    p for p in (Path(__file__).with_name('data') / 'bad-wheels').iterdir()
      if p.suffix == '.whl'
], ids=attrgetter("name"))
def test_verify_bad_wheels(whlfile):
    with open(str(whlfile.with_suffix('.json'))) as fp:
        expected = json.load(fp)
    with Wheel(str(whlfile)) as whl:
        with pytest.raises(WheelValidationError) as excinfo:
            whl.verify_record()
        assert type(excinfo.value).__name__ == expected["type"]
        assert str(excinfo.value) == expected["str"]
