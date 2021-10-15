from io import StringIO
import json
from operator import attrgetter
from pathlib import Path
import pytest
from wheel_inspect.errors import RecordError
from wheel_inspect.record import FileData, load_record


def test_parse_record() -> None:
    assert load_record(
        StringIO(
            """\
qypi/__init__.py,sha256=zgE5-Sk8hED4NRmtnPUuvp1FDC4Z6VWCzJOOZwZ2oh8,532
qypi/__main__.py,sha256=GV5UVn3j5z4x-r7YYEB-quNPCucZYK1JOfWxmbdB0N0,7915
qypi/api.py,sha256=2c4EwxDhhHEloeOIeN0YgpIxCGpZaTDNJMYtHlVCcl8,3867
qypi/util.py,sha256=I2mRemqS5PHe5Iabk-CLrgFB2rznR87dVI3YwvpctSQ,3282

qypi-0.4.1.dist-info/DESCRIPTION.rst,sha256=SbT27FgdGvU8QlauLamstt7g4v7Cr2j6jc4RPr7bKNU,11633
qypi-0.4.1.dist-info/LICENSE.txt,sha256=SDaeT4Cm3ZeLgPOOL_f9BliMMHH_GVwqJa6czCztoS0,1090
qypi-0.4.1.dist-info/METADATA,sha256=msK-_0Fe8JHBjBv4HH35wbpUbIlCYv1Vy3X37tIdY5I,12633
qypi-0.4.1.dist-info/RECORD,,
qypi-0.4.1.dist-info/WHEEL,sha256=rNo05PbNqwnXiIHFsYm0m22u4Zm6YJtugFG2THx4w3g,92
qypi-0.4.1.dist-info/entry_points.txt,sha256=t4_O2VB3V-o52_PLoLLIb8m4SQDmY0HFdEJ9_Q2Odtw,45
qypi-0.4.1.dist-info/metadata.json,sha256=KI5TdfaYL-TPS1dMTABV6S8BFq9iAJRk3rkTXjOdgII,1297
qypi-0.4.1.dist-info/top_level.txt,sha256=J2Q5xVa8BtnOTGxjqY2lKQRB22Ydn9JF2PirqDEKE_Y,5
"""
        )
    ) == {
        "qypi/__init__.py": FileData(
            algorithm="sha256",
            digest="zgE5-Sk8hED4NRmtnPUuvp1FDC4Z6VWCzJOOZwZ2oh8",
            size=532,
        ),
        "qypi/__main__.py": FileData(
            algorithm="sha256",
            digest="GV5UVn3j5z4x-r7YYEB-quNPCucZYK1JOfWxmbdB0N0",
            size=7915,
        ),
        "qypi/api.py": FileData(
            algorithm="sha256",
            digest="2c4EwxDhhHEloeOIeN0YgpIxCGpZaTDNJMYtHlVCcl8",
            size=3867,
        ),
        "qypi/util.py": FileData(
            algorithm="sha256",
            digest="I2mRemqS5PHe5Iabk-CLrgFB2rznR87dVI3YwvpctSQ",
            size=3282,
        ),
        "qypi-0.4.1.dist-info/DESCRIPTION.rst": FileData(
            algorithm="sha256",
            digest="SbT27FgdGvU8QlauLamstt7g4v7Cr2j6jc4RPr7bKNU",
            size=11633,
        ),
        "qypi-0.4.1.dist-info/LICENSE.txt": FileData(
            algorithm="sha256",
            digest="SDaeT4Cm3ZeLgPOOL_f9BliMMHH_GVwqJa6czCztoS0",
            size=1090,
        ),
        "qypi-0.4.1.dist-info/METADATA": FileData(
            algorithm="sha256",
            digest="msK-_0Fe8JHBjBv4HH35wbpUbIlCYv1Vy3X37tIdY5I",
            size=12633,
        ),
        "qypi-0.4.1.dist-info/RECORD": None,
        "qypi-0.4.1.dist-info/WHEEL": FileData(
            algorithm="sha256",
            digest="rNo05PbNqwnXiIHFsYm0m22u4Zm6YJtugFG2THx4w3g",
            size=92,
        ),
        "qypi-0.4.1.dist-info/entry_points.txt": FileData(
            algorithm="sha256",
            digest="t4_O2VB3V-o52_PLoLLIb8m4SQDmY0HFdEJ9_Q2Odtw",
            size=45,
        ),
        "qypi-0.4.1.dist-info/metadata.json": FileData(
            algorithm="sha256",
            digest="KI5TdfaYL-TPS1dMTABV6S8BFq9iAJRk3rkTXjOdgII",
            size=1297,
        ),
        "qypi-0.4.1.dist-info/top_level.txt": FileData(
            algorithm="sha256",
            digest="J2Q5xVa8BtnOTGxjqY2lKQRB22Ydn9JF2PirqDEKE_Y",
            size=5,
        ),
    }


@pytest.mark.parametrize(
    "recfile",
    (Path(__file__).with_name("data") / "bad-records").glob("*.csv"),
    ids=attrgetter("name"),
)
def test_parse_bad_records(recfile: Path) -> None:
    with recfile.with_suffix(".json").open() as fp:
        expected = json.load(fp)
    with recfile.open(newline="") as fp:
        with pytest.raises(RecordError) as excinfo:
            load_record(fp)
        assert type(excinfo.value).__name__ == expected["type"]
        assert str(excinfo.value) == expected["str"]
