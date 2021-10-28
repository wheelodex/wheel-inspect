import json
from operator import attrgetter
from pathlib import Path
import pytest
from testing_lib import DATA_DIR
from wheel_inspect.consts import PathType
from wheel_inspect.errors import NoSuchPathError, NotDirectoryError, RecordError
from wheel_inspect.record import FileData, Record, RecordPath
from wheel_inspect.util import for_json


def test_parse_record() -> None:
    with (DATA_DIR / "records" / "qypi.csv").open() as fp:
        r = Record.load(fp)
    data = {
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
    assert dict(r) == data
    assert len(r) == len(data)
    assert repr(r) == f"Record({data!r})"
    assert "qypi/__init__.py" in r
    assert r["qypi/__init__.py"] == FileData(
        algorithm="sha256",
        digest="zgE5-Sk8hED4NRmtnPUuvp1FDC4Z6VWCzJOOZwZ2oh8",
        size=532,
    )
    assert "qypi-0.4.1.dist-info/RECORD" in r
    assert r["qypi-0.4.1.dist-info/RECORD"] is None
    for name in ["qypi", "qypi/", "foo"]:
        assert name not in r
        with pytest.raises(KeyError) as excinfo:
            r[name]
        assert str(excinfo.value) == repr(name)
    assert r.dist_info_dirname == "qypi-0.4.1.dist-info"
    assert r.data_dirname is None


def test_recordpath() -> None:
    with (DATA_DIR / "records" / "netkiller-devops.csv").open() as fp:
        r = Record.load(fp)
    assert r.dist_info_dirname == "netkiller_devops-0.2.6.dist-info"
    assert r.data_dirname == "netkiller_devops-0.2.6.data"

    root = r.filetree
    assert isinstance(root, RecordPath)
    assert root.parts == ()
    assert root.name == ""
    assert root.stem == ""
    assert root.suffix == ""
    assert root.parent is root
    assert root.parents == ()
    assert str(root) == ""
    assert repr(root) == "RecordPath('', filedata=None)"
    assert root.exists()
    assert root.is_dir()
    assert root.is_root()
    assert root.root_path is root
    assert sorted(p.name for p in root.iterdir()) == [
        "netkiller",
        "netkiller_devops-0.2.6.data",
        "netkiller_devops-0.2.6.dist-info",
    ]
    assert root.filedata is None
    assert root.path_type is PathType.DIRECTORY
    with pytest.raises(ValueError):
        root.with_suffix(".txt")

    netkiller = root / "netkiller"
    assert netkiller.parts == ("netkiller",)
    assert netkiller.name == "netkiller"
    assert netkiller.stem == "netkiller"
    assert netkiller.suffix == ""
    assert netkiller.parent == root
    assert netkiller.parents == (root,)
    assert (netkiller / ".") is netkiller
    assert (netkiller / "..") is root
    assert str(netkiller) == "netkiller"
    assert repr(netkiller) == "RecordPath('netkiller', filedata=None)"
    assert netkiller.exists()
    assert netkiller.is_dir()
    assert not netkiller.is_root()
    assert netkiller.root_path is root
    assert sorted(p.name for p in netkiller.iterdir()) == [
        "__init__.py",
        "docker.py",
        "git.py",
        "kubernetes.py",
        "nagios.py",
        "rsync.py",
        "wework.py",
        "whiptail.py",
    ]
    assert netkiller.filedata is None
    assert netkiller.with_suffix(".txt") == root / "netkiller.txt"
    for s in [".txt/", "/.txt", ".t/xt", ".", "foo"]:
        with pytest.raises(ValueError) as excinfo:
            netkiller.with_suffix(s)
        assert str(excinfo.value) == f"Invalid suffix: {s!r}"

    initfile = netkiller / "__init__.py"
    assert initfile == root / "netkiller" / "__init__.py"
    assert initfile == root / "netkiller/__init__.py"
    assert initfile.parts == ("netkiller", "__init__.py")
    assert initfile.name == "__init__.py"
    assert initfile.parent == netkiller
    assert initfile.parents == (netkiller, root)
    assert str(initfile) == "netkiller/__init__.py"
    assert (
        repr(initfile)
        == "RecordPath('netkiller/__init__.py', filedata=FileData(size=71, algorithm='sha256', digest='4KCG6HW6TFtOVNi6qv2avEnqWto9dGgvRrT78R1aq0c'))"
    )
    assert initfile.exists()
    assert initfile.is_file()
    assert not initfile.is_root()
    assert initfile.root_path is root
    assert initfile.filedata == FileData(
        size=71,
        algorithm="sha256",
        digest="4KCG6HW6TFtOVNi6qv2avEnqWto9dGgvRrT78R1aq0c",
    )
    assert initfile.path_type is PathType.FILE
    with pytest.raises(NotDirectoryError):
        next(initfile.iterdir())
    with pytest.raises(NotDirectoryError):
        initfile / "foo"
    with pytest.raises(NotDirectoryError):
        initfile / "."
    with pytest.raises(NotDirectoryError):
        initfile / ".."

    nexist = netkiller / "nexist"
    assert nexist.parts == ("netkiller", "nexist")
    assert nexist.name == "nexist"
    assert nexist.parent is netkiller
    assert str(nexist) == "netkiller/nexist"
    assert not nexist.exists()
    with pytest.raises(NoSuchPathError):
        nexist.path_type
    with pytest.raises(NoSuchPathError):
        next(nexist.iterdir())
    # Assert the parent wasn't modified:
    assert sorted(p.name for p in netkiller.iterdir()) == [
        "__init__.py",
        "docker.py",
        "git.py",
        "kubernetes.py",
        "nagios.py",
        "rsync.py",
        "wework.py",
        "whiptail.py",
    ]

    dist_info = root / r.dist_info_dirname
    assert sorted(p.name for p in dist_info.iterdir()) == [
        "LICENSE",
        "METADATA",
        "RECORD",
        "WHEEL",
        "top_level.txt",
    ]
    assert (dist_info / "RECORD").exists()
    assert (dist_info / "RECORD").filedata is None

    data_dir = root / r.data_dirname
    assert sorted(p.name for p in data_dir.iterdir()) == ["data", "scripts"]

    datalib = data_dir / "data"
    assert datalib.parts == ("netkiller_devops-0.2.6.data", "data")
    assert datalib.name == "data"
    assert datalib.parent is data_dir
    assert (datalib / ".") is datalib
    assert (datalib / "..") is data_dir
    assert str(datalib) == "netkiller_devops-0.2.6.data/data"
    assert datalib.exists()
    assert not datalib.is_root()
    assert datalib.root_path is root
    assert sorted(p.name for p in datalib.iterdir()) == ["etc", "libexec", "share"]

    devops = datalib / "share" / "devops.sh"
    assert devops.root_path == root
    assert devops.parts == (
        "netkiller_devops-0.2.6.data",
        "data",
        "share",
        "devops.sh",
    )
    assert str(devops) == "netkiller_devops-0.2.6.data/data/share/devops.sh"
    assert devops.suffix == ".sh"
    assert devops.suffixes == [".sh"]
    assert devops.stem == "devops"
    assert devops.with_name("example.com.ini") == datalib / "share" / "example.com.ini"
    assert devops.with_suffix(".tar") == datalib / "share" / "devops.tar"
    assert devops.with_suffix(".tar.gz") == datalib / "share" / "devops.tar.gz"
    assert devops.with_suffix("") == datalib / "share" / "devops"

    devops2 = datalib.joinpath("libexec", "devops")
    mysql_gpg_sh = devops2 / "backup.mysql.gpg.sh"
    assert mysql_gpg_sh.name == "backup.mysql.gpg.sh"
    assert mysql_gpg_sh.suffix == ".sh"
    assert mysql_gpg_sh.suffixes == [".mysql", ".gpg", ".sh"]
    assert mysql_gpg_sh.stem == "backup.mysql.gpg"
    assert mysql_gpg_sh.with_name("foo") == devops2 / "foo"
    assert mysql_gpg_sh.with_stem("foo") == devops2 / "foo.sh"
    assert mysql_gpg_sh.with_suffix(".txt") == devops2 / "backup.mysql.gpg.txt"
    assert mysql_gpg_sh.with_suffix("") == devops2 / "backup.mysql.gpg"
    assert mysql_gpg_sh.match("*.sh")
    assert mysql_gpg_sh.match("backup.*.sh")
    assert mysql_gpg_sh.match("backup.*")
    assert not mysql_gpg_sh.match("*.gpg")
    assert mysql_gpg_sh.match("*/*/*.sh")
    assert mysql_gpg_sh.match("*.data/data/*/*/*.sh")
    assert not mysql_gpg_sh.match("*.data/data/*/*/*/*.sh")
    with pytest.raises(ValueError):
        mysql_gpg_sh.match("/*.data/data/*/*/*.sh")
    with pytest.raises(ValueError):
        mysql_gpg_sh.match("")


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
            Record.load(fp)
        assert for_json(excinfo.value) == expected


def test_file_data_digests() -> None:
    fd = FileData(
        algorithm="sha256",
        digest="zgE5-Sk8hED4NRmtnPUuvp1FDC4Z6VWCzJOOZwZ2oh8",
        size=532,
    )
    assert fd.b64_digest == "zgE5-Sk8hED4NRmtnPUuvp1FDC4Z6VWCzJOOZwZ2oh8"
    assert (
        fd.hex_digest
        == "ce0139f9293c8440f83519ad9cf52ebe9d450c2e19e95582cc938e670676a21f"
    )
    assert fd.bytes_digest == bytes.fromhex(
        "ce0139f9293c8440f83519ad9cf52ebe9d450c2e19e95582cc938e670676a21f"
    )
