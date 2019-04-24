from read_version import read_version
from setuptools   import setup

setup(version=read_version('src', 'wheel_inspect', '__init__.py'))
