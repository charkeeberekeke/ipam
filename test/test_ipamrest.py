import os
import json
import sys

from nose.tools import ok_, eq_, raises, with_setup
from lxml import etree

try:
    from ipam.domain import *
    from ipamrest import app
except ImportError:
    sys.path.append(os.path.abspath(".."))
    from ipamrest import app
    from ipam.domain import *

class TestRestAPI:
    def setUp(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

    def test_sample(self):
        tmp = self.app.get("ipam/api/v1.0/domain/Sedgman")
        print tmp.get_data()
