import pytest
from testing_lib import filecases
from wheel_inspect.inspecting import parse_entry_points
from wheel_inspect.metadata import parse_metadata
from wheel_inspect.wheel_info import parse_wheel_info


@pytest.mark.parametrize("mdfile,expected", filecases("metadata", "*.metadata"))
def test_parse_metadata(mdfile, expected):
    with mdfile.open(encoding="utf-8") as fp:
        assert parse_metadata(fp) == expected


@pytest.mark.parametrize("epfile,expected", filecases("entry_points", "*.txt"))
def test_parse_entry_points(epfile, expected):
    with epfile.open(encoding="utf-8") as fp:
        assert parse_entry_points(fp) == expected


@pytest.mark.parametrize("wifile,expected", filecases("wheel_info", "*.wheel"))
def test_parse_wheel_info(wifile, expected):
    with wifile.open(encoding="utf-8") as fp:
        assert parse_wheel_info(fp) == expected
