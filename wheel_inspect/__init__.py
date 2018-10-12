"""
Extract information from wheels

Visit <https://github.com/jwodder/wheel-inspect> for more information.
"""

from .inspect import inspect_wheel
from .schema  import SCHEMA

__version__      = '1.0.0.dev1'
__author__       = 'John Thorvald Wodder II'
__author_email__ = 'wheel-inspect@varonathe.org'
__license__      = 'MIT'
__url__          = 'https://github.com/jwodder/wheel-inspect'

__all__ = [
    'SCHEMA',
    'inspect_wheel',
]
