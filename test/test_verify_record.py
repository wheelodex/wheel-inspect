import json
from   operator                 import attrgetter
from   pathlib                  import Path
import pytest
from   wheel_inspect.classes    import WheelFile
from   wheel_inspect.errors     import WheelValidationError
from   wheel_inspect.inspecting import verify_record

@pytest.mark.parametrize('whlfile', [
    p for p in (Path(__file__).with_name('data') / 'bad-wheels').iterdir()
      if p.suffix == '.whl'
], ids=attrgetter("name"))
def test_verify_bad_wheels(whlfile):
    with whlfile.with_suffix('.json').open() as fp:
        expected = json.load(fp)
    with WheelFile(whlfile) as whl:
        with pytest.raises(WheelValidationError) as excinfo:
            verify_record(whl, whl.get_record())
        assert type(excinfo.value).__name__ == expected["type"]
        assert str(excinfo.value) == expected["str"]
