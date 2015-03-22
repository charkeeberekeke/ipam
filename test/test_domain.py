import os
import json
import sys

from nose.tools import ok_, eq_, raises, with_setup

from lxml import etree

try:
    from ipam.domain import *
except ImportError:
    sys.path.append(os.path.abspath(".."))
    from ipam.domain import *

class TestDomain:
    def __init__(self):
        self.test_domain = {"Sedgman": ["Region", "City"]}
        self.file = "test.json" 
        with open(self.file, "w") as f:
            json.dump(self.test_domain, f)
        self.schema = Schema(self.file)
        self.domain = Domain(domain="Sedgman", groups=self.schema.get_groups("Sedgman"))

    def reset(self):
        self.domain = Domain(domain="Sedgman", groups=self.schema.get_groups("Sedgman"))
        parent = self.domain.add_node(node_type="Region", name="Australia", network="10.0.0.0/12")
        self.domain.add_node(node_type="City", name="Brisbane", network="10.0.0.0/19", parent=parent)

    def test_create_domain(self):
        eq_(self.domain.domain, self.domain.root.get('name'))

    def test_create_node_1(self):
        node = self.domain.add_node(node_type="Region", name="Australia", network="10.0.0.0/12")
        ok_(self.domain.root[0] == node)

    @raises(InvalidNodeTypeError)
    def test_create_node_2(self):
        self.domain.add_node(node_type="Error", name="Europe")

    @raises(CantAddParentlessNodeError)
    def test_create_node_3(self):
        self.domain.add_node(node_type="City", name="Melbourne")

    @raises(DuplicateSiblingError)
    def test_create_node_4(self):
        self.reset()
        parent = self.domain.get_node(node_type="Region", name="Australia")[0]
        self.domain.add_node(node_type="City", name="brisbane", network="10.14.0.0/16", parent=parent)

    @raises(DuplicateSiblingError)
    def test_create_node_5(self):
        self.reset()
        parent = self.domain.get_node(node_type="Region", name="Australia")[0]
        self.domain.add_node(node_type="City", name="Mackay", network="10.0.0.0/19", parent=parent)

    @raises(DuplicateSiblingError)
    def test_create_node_6(self):
        self.reset()
        parent = self.domain.get_node(node_type="Region", name="Australia")[0]
        self.domain.add_node(node_type="City", name="Mackay", network="10.0.3.0/24", parent=parent)

    @raises(InvalidIPError)
    def test_ip_validate(self):
        self.domain.add_node(node_type="Region", name="Asia", network="non-IP string")

    def test_get_node(self):
        n1 = self.domain.add_node(node_type="Region", name="Chile", network="10.64.0.0/12")
        n2 = self.domain.get_node(node_type="Region", name="Chile")
        eq_(n1, n2[0])

    @raises(AssignedIPnotinSubnet)
    def test_child_subnet_validate(self):
        parent = self.domain.add_node(node_type="Region", name="Asia", network="10.16.0.0/12")
        self.domain.add_node(node_type="City", name="Shanghai", network="10.128.0.0/21", parent=parent)

    def test_child_subnet_validate2(self):
        parent = self.domain.add_node(node_type="Region", name="Africa", network="10.32.0.0/12")
        node = self.domain.add_node(node_type="City", name="South Africa", network="10.32.0.0/12", parent=parent)
        ok_(node.get("network") == "10.32.0.0/12")

    def test_child_subnet_validate3(self):
        parent = self.domain.add_node(node_type="Region", name="Canada", network="")
        n = self.domain.add_node(node_type="City", name="Vancouver", network="10.80.0.0/21", parent=parent)
        ok_(n is not None)

    @raises(AssignedIPnotinSubnet)
    def test_child_subnet_validate4(self):
        parent = self.domain.add_node(node_type="Region", name="Unites States", network="10.96.0.0/12")
        n = self.domain.add_node(node_type="City", name="New Jersey", parent=parent)

    def test_set_node_change_name(self):
        self.reset()
        node = self.domain.get_node(node_type="City", name="Brisbane")
        node = self.domain.set_node(node[0], name="Perth")
        eq_(node.get("name"), "Perth")

    @raises(AssignedIPnotinSubnet)
    def test_set_node_change_network_1(self):
        self.reset()
        node = self.domain.get_node(node_type="City", name="Brisbane")
        node = self.domain.set_node(node[0], network="10.16.0.0/16")

    @raises(AssignedIPnotinSubnet)
    def test_set_node_change_network_2(self):
        self.reset()
        node = self.domain.get_node(node_type="Region", name="Australia")
        node = self.domain.set_node(node[0], network="10.32.0.0/16")

    @raises(ConfirmDeleteNodeError)
    def test_remove_node_1(self):
        self.reset()
        node = self.domain.get_node(node_type="Region", name="Australia")
        self.domain.remove_node(node[0])

    def test_remove_node_2(self):
        self.reset()
        node = self.domain.get_node(node_type="Region", name="Australia")
        self.domain.remove_node(node[0], force=True)
        node = self.domain.get_node(node_type="City", name="Brisbane")
        ok_(node == [])
        node = self.domain.get_node(node_type="Region", name="Australia")
        ok_(node == [])

    def test_search_network(self):
        self.reset()
        parent = self.domain.add_node(node_type="Region", name="Asia", network="10.16.0.0/12")
        child1 = self.domain.add_node(node_type="City", name="Shanghai", network="10.16.0.0/19", parent=parent)
        child2 = self.domain.add_node(node_type="City", name="Beijing", network="10.17.0.0/19", parent=parent)
        n = self.domain._search_network(network="10.16.20.0/24", node=self.domain.root)
        eq_(n, child1)
        n = self.domain._search_network(network="10.0.9.0/24", node=self.domain.root)
        eq_(n, self.domain.get_node(node_type="City", name="Brisbane")[0])
        n = self.domain._search_network(network="10.128.0.0/24", node=self.domain.root)
        eq_(n, self.domain.root)
