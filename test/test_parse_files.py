import json
from   operator                 import attrgetter
from   pathlib                  import Path
import pytest
from   wheel_inspect.metadata   import parse_metadata
from   wheel_inspect.wheel_info import parse_wheel_info
from   wheel_inspect.wheelcls   import parse_entry_points

@pytest.mark.parametrize('mdfile', [
    p for p in (Path(__file__).with_name('data') / 'metadata').iterdir()
      if p.suffix == '.metadata'
], ids=attrgetter("name"))
def test_parse_metadata(mdfile):
    with open(str(mdfile.with_suffix('.json'))) as fp:
        expected = json.load(fp)
    with open(str(mdfile), encoding='utf-8') as fp:
        assert parse_metadata(fp) == expected

@pytest.mark.parametrize('epfile', [
    p for p in (Path(__file__).with_name('data') / 'entry_points').iterdir()
      if p.suffix == '.txt'
], ids=attrgetter("name"))
def test_parse_entry_points(epfile):
    with open(str(epfile.with_suffix('.json'))) as fp:
        expected = json.load(fp)
    with open(str(epfile), encoding='utf-8') as fp:
        assert parse_entry_points(fp) == expected

@pytest.mark.parametrize('wifile', [
    p for p in (Path(__file__).with_name('data') / 'wheel_info').iterdir()
      if p.suffix == '.wheel'
], ids=attrgetter("name"))
def test_parse_wheel_info(wifile):
    with open(str(wifile.with_suffix('.json'))) as fp:
        expected = json.load(fp)
    with open(str(wifile), encoding='utf-8') as fp:
        assert parse_wheel_info(fp) == expected
