import pytest
from testing_lib import DATA_DIR
from wheel_inspect import PathType, Tree, WheelFile
from wheel_inspect.classes import BackedTreePath
from wheel_inspect.errors import NoSuchPathError, NotDirectoryError
from wheel_inspect.record import FileData


def test_backedfiletree() -> None:
    with WheelFile.from_path(
        DATA_DIR / "wheels" / "netkiller_devops-0.2.6-py3-none-any.whl"
    ) as whl:
        assert set(whl.filetrees) == {
            Tree.ALL,
            Tree.PURELIB,
            Tree.DATA,
            Tree.DIST_INFO,
            "scripts",
            "data",
        }
        assert len(whl.filetrees) == 6

        purelib = whl.filetrees[Tree.PURELIB]
        assert isinstance(purelib, BackedTreePath)
        assert purelib.parts == ()
        assert purelib.name == ""
        assert purelib.stem == ""
        assert purelib.suffix == ""
        assert purelib.parent is purelib
        assert purelib.parents == ()
        assert purelib.tree_id is Tree.PURELIB
        assert str(purelib) == ""
        assert repr(purelib) == "BackedTreePath('', tree_id=Tree.PURELIB)"
        assert purelib.exists()
        assert purelib.is_dir()
        assert purelib.is_root()
        assert purelib.root_path is purelib
        assert sorted(p.name for p in purelib.iterdir()) == ["netkiller"]
        assert purelib.filedata is None
        assert purelib.path_type is PathType.DIRECTORY
        with pytest.raises(ValueError):
            purelib.with_suffix(".txt")

        netkiller = purelib / "netkiller"
        assert netkiller.parts == ("netkiller",)
        assert netkiller.name == "netkiller"
        assert netkiller.stem == "netkiller"
        assert netkiller.suffix == ""
        assert netkiller.parent == purelib
        assert netkiller.parents == (purelib,)
        assert (netkiller / ".") is netkiller
        assert (netkiller / "..") == purelib
        assert netkiller.tree_id is Tree.PURELIB
        assert str(netkiller) == "netkiller"
        assert repr(netkiller) == "BackedTreePath('netkiller', tree_id=Tree.PURELIB)"
        assert netkiller.exists()
        assert netkiller.is_dir()
        assert not netkiller.is_root()
        assert netkiller.root_path == purelib
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
        assert netkiller.path_type is PathType.DIRECTORY
        netkiller.verify()
        assert netkiller.with_suffix(".txt") == purelib / "netkiller.txt"
        for s in [".txt/", "/.txt", ".t/xt", ".", "foo"]:
            with pytest.raises(ValueError) as excinfo:
                netkiller.with_suffix(s)
            assert str(excinfo.value) == f"Invalid suffix: {s!r}"

        initfile = netkiller / "__init__.py"
        assert initfile == purelib / "netkiller" / "__init__.py"
        assert initfile == purelib / "netkiller/__init__.py"
        assert initfile.parts == ("netkiller", "__init__.py")
        assert initfile.name == "__init__.py"
        assert initfile.parent == netkiller
        assert initfile.parents == (netkiller, purelib)
        assert initfile.tree_id is Tree.PURELIB
        assert str(initfile) == "netkiller/__init__.py"
        assert (
            repr(initfile)
            == "BackedTreePath('netkiller/__init__.py', tree_id=Tree.PURELIB)"
        )
        assert initfile.exists()
        assert initfile.is_file()
        assert not initfile.is_root()
        assert initfile.root_path == purelib
        assert (
            initfile.read_text(encoding="utf-8")
            == "__version__ = '1.1.0'\n__author__ = 'Neo Chen'\n__all__ = ['docker','.']\n"
        )
        assert initfile.filedata == FileData(
            size=71,
            algorithm="sha256",
            digest="4KCG6HW6TFtOVNi6qv2avEnqWto9dGgvRrT78R1aq0c",
        )
        assert initfile.path_type is PathType.FILE
        initfile.verify()
        with pytest.raises(NotDirectoryError):
            list(initfile.iterdir())
        with pytest.raises(NotDirectoryError):
            initfile / "foo"
        with pytest.raises(NotDirectoryError):
            initfile / "."
        with pytest.raises(NotDirectoryError):
            initfile / ".."

        pure_dist = purelib / "netkiller_devops-0.2.6.dist-info"
        assert pure_dist.parts == ("netkiller_devops-0.2.6.dist-info",)
        assert pure_dist.name == "netkiller_devops-0.2.6.dist-info"
        assert pure_dist.parent == purelib
        assert pure_dist.tree_id is Tree.PURELIB
        assert str(pure_dist) == "netkiller_devops-0.2.6.dist-info"
        assert not pure_dist.exists()
        with pytest.raises(NoSuchPathError):
            pure_dist.path_type
        with pytest.raises(NoSuchPathError):
            list(pure_dist.iterdir())
        assert sorted(p.name for p in purelib.iterdir()) == ["netkiller"]

        assert whl.filetrees[Tree.ROOT] is purelib

        alltree = whl.filetrees[Tree.ALL]
        assert alltree != purelib
        assert alltree.tree_id is Tree.ALL
        assert sorted(p.name for p in alltree.iterdir()) == [
            "netkiller",
            "netkiller_devops-0.2.6.data",
            "netkiller_devops-0.2.6.dist-info",
        ]

        dist_info = whl.filetrees[Tree.DIST_INFO]
        assert sorted(p.name for p in dist_info.iterdir()) == [
            "LICENSE",
            "METADATA",
            "RECORD",
            "WHEEL",
            "top_level.txt",
        ]
        assert (dist_info / "RECORD").exists()
        assert (dist_info / "RECORD").filedata is None

        data_dir = whl.filetrees[Tree.DATA]
        assert sorted(p.name for p in data_dir.iterdir()) == ["data", "scripts"]

        datalib = whl.filetrees["data"]
        assert isinstance(datalib, BackedTreePath)
        assert datalib.parts == ("netkiller_devops-0.2.6.data", "data")
        assert datalib.name == ""
        assert datalib.parent is datalib
        assert (datalib / ".") is datalib
        assert (datalib / "..") is datalib
        assert datalib.tree_id == "data"
        assert str(datalib) == "netkiller_devops-0.2.6.data/data"
        assert (
            repr(datalib)
            == "BackedTreePath('netkiller_devops-0.2.6.data/data', tree_id='data')"
        )
        assert datalib.exists()
        assert datalib.relative_parts == ()
        assert datalib.relative_path == ""
        assert datalib.is_root()
        assert datalib.root_path is datalib
        assert sorted(p.name for p in datalib.iterdir()) == ["etc", "libexec", "share"]

        devops = datalib / "share" / "devops.sh"
        assert devops.root_path == datalib
        assert (
            devops.read_text(encoding="utf-8") == "export PATH=$PATH:/srv/devops/bin\n"
        )
        assert devops.parts == (
            "netkiller_devops-0.2.6.data",
            "data",
            "share",
            "devops.sh",
        )
        assert str(devops) == "netkiller_devops-0.2.6.data/data/share/devops.sh"
        assert (
            repr(devops)
            == "BackedTreePath('netkiller_devops-0.2.6.data/data/share/devops.sh', tree_id='data')"
        )
        assert devops.relative_parts == ("share", "devops.sh")
        assert devops.relative_path == "share/devops.sh"
        assert devops.suffix == ".sh"
        assert devops.suffixes == [".sh"]
        assert devops.stem == "devops"
        assert (
            devops.with_name("example.com.ini") == datalib / "share" / "example.com.ini"
        )
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

        with pytest.raises(KeyError):
            whl.filetrees["purelib"]
        with pytest.raises(KeyError):
            whl.filetrees[Tree.PLATLIB]
        with pytest.raises(KeyError):
            whl.filetrees["platlib"]
        with pytest.raises(KeyError):
            whl.filetrees["headers"]
        with pytest.raises(KeyError):
            whl.filetrees["foobar"]
        with pytest.raises(KeyError):
            whl.filetrees["scripts/"]
        with pytest.raises(KeyError):
            whl.filetrees["/scripts"]
        with pytest.raises(KeyError):
            whl.filetrees[""]
        with pytest.raises(KeyError):
            whl.filetrees["."]
        with pytest.raises(KeyError):
            whl.filetrees[".."]
