import json
from   operator                 import attrgetter
from   pathlib                  import Path
import pytest
from   wheel_inspect.inspecting import parse_entry_points
from   wheel_inspect.metadata   import parse_metadata
from   wheel_inspect.wheel_info import parse_wheel_info

@pytest.mark.parametrize('mdfile', [
    p for p in (Path(__file__).with_name('data') / 'metadata').iterdir()
      if p.suffix == '.metadata'
], ids=attrgetter("name"))
def test_parse_metadata(mdfile):
    with mdfile.with_suffix('.json').open() as fp:
        expected = json.load(fp)
    with mdfile.open(encoding='utf-8') as fp:
        assert parse_metadata(fp) == expected

@pytest.mark.parametrize('epfile', [
    p for p in (Path(__file__).with_name('data') / 'entry_points').iterdir()
      if p.suffix == '.txt'
], ids=attrgetter("name"))
def test_parse_entry_points(epfile):
    with epfile.with_suffix('.json').open() as fp:
        expected = json.load(fp)
    with epfile.open(encoding='utf-8') as fp:
        assert parse_entry_points(fp) == expected

@pytest.mark.parametrize('wifile', [
    p for p in (Path(__file__).with_name('data') / 'wheel_info').iterdir()
      if p.suffix == '.wheel'
], ids=attrgetter("name"))
def test_parse_wheel_info(wifile):
    with wifile.with_suffix('.json').open() as fp:
        expected = json.load(fp)
    with wifile.open(encoding='utf-8') as fp:
        assert parse_wheel_info(fp) == expected
