import os
import json
import sys

from nose.tools import ok_, eq_, raises

try:
    from ipam.schema import *
except ImportError:
    sys.path.append(os.path.abspath(".."))
    from ipam.schema import *

class TestSchema:
    def setUp(self):
        self.test_domain = {"domain1" : ["group1", "group2"], 
                            "domain10" : ["group10", "group11", "group12"],
                            "domain20" : ["group21", "group22", "group23"]}
        self.file = "test.json" 
        with open(self.file, "w") as f:
            json.dump(self.test_domain, f)
        self.schema = Schema(self.file)

    def test_domains_in_schema_json(self):
        keys = self.schema.get_domains()
        for k in self.test_domain.keys(): 
            ok_(k in keys, "Testing domains from schema json")

    @raises(DomainAlreadyExistsError)
    def test_cannot_overwrite_new_domain(self):
        self.schema.new_domain("domain1")

    def test_ensure_domain_group_is_a_list(self):
        self.schema.new_domain("domain30")
        ok_(isinstance(self.schema.get_groups("domain30"), list))

    @raises(DomainDoesNotExistError)
    def test_cannot_get_group_from_nonexistent_domain(self):
        self.schema.get_groups("domain30")

    @raises(InvalidGroupError)
    def test_assert_domain_group_is_a_list(self):
        self.schema.update_domain("domain30", "not a list")

    @raises(InvalidDomainError)
    def test_assert_domain_struct_is_a_dict(self):
        self.schema.load([])

    @raises(InvalidGroupError)
    def test_assert_domain_group_is_a_list_in_a_load_function(self):
        self.schema.load({"test" : "not a list"})

    def tearDown(self): 
        os.remove(self.file)
        pass
