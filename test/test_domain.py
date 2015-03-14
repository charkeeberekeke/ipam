import os
import json
import sys

from nose.tools import ok_, eq_, raises

try:
    from ipam.domain import *
except ImportError:
    sys.path.append(os.path.abspath(".."))
    from ipam.domain import *
