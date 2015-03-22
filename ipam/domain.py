from lxml import etree
from schema import *
from ipaddr import IPv4Address, IPv4Network

"""
snippet for pathnames
PATH = os.path.dirname(os.path.realpath(__file__))
PACKAGES = os.path.join(PATH, "packages")
SHELL = os.path.join(PATH, "shell")
HOME = os.path.expanduser("~")
LOG = os.path.join(HOME, "log")
"""

class InvalidIPError(Exception):
    pass

class AssignedIPnotinSubnet(Exception):
    pass

class InvalidNodeTypeError(Exception):
    pass

class CantAddParentlessNodeError(Exception):
    pass

class ConfirmDeleteNodeError(Exception):
    pass

class DuplicateSiblingError(Exception):
    pass

class Domain:
    """
    Container class for domain object with an etree representation of xml structure of nodes and networks
    """

    def __init__(self, domain=None, groups=None, path_to_xml=None):
        """
        Initialize object with domain name. Class will open xml file with name 'domain.xml'. 
        If no file is present, set file object none
        and initialize tree structure
        """
        self.file = None
        self.domain = domain
        self.path_to_xml = path_to_xml
        self.groups = groups or []
        self.root = None

        if self.path_to_xml:
            self.file = os.path.join(self.path_to_xml, "%s.xml" % domain)
            try:
                # parse xml file and extract domain name from root element with tag domain
                # set self.domain to extracted domain as well as self.file as file
                # set self.root to tree root
                # exit __init__
                pass
            except IOError:  # insert XMLparsingerror
                pass

        if self.domain:
            self.root = etree.Element("domain", name=self.domain)
            if self.path_to_xml:
                self.file = os.path.join(self.path_to_xml, "%s.xml" % domain)
        else:
            self.root = etree.Element("domain")

    def _validated_ip(self, ip):
        """
        Validates IP address argument
        Accepts ip address in string format, returns None if invalid ip
        otherwise return IPv4Network object representing ip
        """
        ip = (ip == "") and "0.0.0.0/0" or ip
        try:
            net = IPv4Network(ip)
        except:
            raise InvalidIPError(ip) 
            #return None
        else:
            return net

    def _is_subnet(self, supernet, net, raise_exception=True):
        """
        Tests if net is subnet of supernet.
        Does the native test in IPv4Address as well as ensure net prefix is longer than supernet
        """
        _super = IPv4Network(supernet)
        _net = IPv4Network(net)
        #return (_net in _super) and (_net.prefixlen > _super.prefixlen)
        if (_net in _super) and (_net.prefixlen >= _super.prefixlen):
            return True
        else:
            if raise_exception:
                raise AssignedIPnotinSubnet("%s in %s" % (net, supernet)) 
            else:
                return False

    def _is_unique_amongst_siblings(self, name=None, network=None, parent=None):
        """
        determines whether provided name and network are unique among given parent's children nodes
        network parameter should already be validated by calling function add_node
        name comparision is case-insensitive
        """
        ret = False
        if isinstance(parent, etree._Element):
            test_name = name.lower()
            for s in parent:
                _name = s.get("name")
                _network = s.get("network")
                if test_name == _name.lower():
                    raise DuplicateSiblingError("name:%s" % name)
                if self._is_subnet(s.get("network"), network, raise_exception=False) or (IPv4Network(network) == IPv4Network(_network)):
                    raise DuplicateSiblingError("network:%s" % _network)

            ret = True

        return ret    

    def add_node(self, node_type=None, parent=None, name="", network=""):
        """
        Add node into the tree. Node type must conform to the schema.
        Return element represeting the node
        """
        child = None
        network = self._validated_ip(network) and network or "0.0.0.0/0"

        if node_type not in self.groups:
            raise InvalidNodeTypeError(node_type)

        if name:
            """
            Test for the following conditions:
            (1) parent is an etree element instance
            (2) node_type is direct descendant/child of parent node_type
            (3) network is a subnet of parent network
            (4) name/network is unique amongst siblings
            """
            if (isinstance(parent, etree._Element) and (self.groups.index(node_type) == self.groups.index(parent.tag) + 1) 
                    and self._is_subnet(parent.get("network"), network) and self._is_unique_amongst_siblings(name=name, network=network, parent=parent)):
                child = etree.Element(node_type, name=name, network=network)
                parent.append(child)
            elif parent is None:
                if self.groups.index(node_type) != 0:
                    raise CantAddParentlessNodeError(node_type)
                child = etree.Element(node_type, name=name, network=network)
                self.root.append(child)

        return child

    def get_node(self, node_type=None, name=None, network=None):
        """
        Return node/s with given properties 
        """
        node = []
        if node_type and (node_type in self.groups):
            if name:
                q = "//%s[@name='%s']" % (node_type, name)
            else:
                q = "//%s" % node_type
            node = self.root.xpath(q)
        elif network: # may need to improve the logic behind selection of name/nodetype vs network search
            pass

        return node

    def _search_network(self, network, node):
        for c in node.getchildren():
            try:
                if self._is_subnet(c.get("network"), network):
                    node = self._search_network(network, c)
            except AssignedIPnotinSubnet:
                continue

        return node
        
    def set_node(self, node=None, **kwargs):
        """
        Change given node according to new properties set in kwargs
        Can change node name safely
        Node_type change not allowed
        Network change  will involve validation for ip address rules
        """
        ret = None
        if isinstance(node, etree._Element):
            # add a case for changing root element attribute(s)
            if "network" in kwargs and self._validated_ip(kwargs["network"]):
                if len(node): 
                    # if node has children, may need to research more reliable way of doing this
                    for c in node.getchildren():
                        if not self._is_subnet(kwargs["network"], c.get("network")):
                            return ret
                if self.groups.index(node.tag) and not self._is_subnet(node.getparent().get("network"), kwargs["network"]):
                    # if node_type is not first in group and node is not subnet of parent node network
                    return ret
                node.set("network", kwargs["network"])
                ret = node
            if "name" in kwargs:
                node.set("name", kwargs["name"])
                ret = node

        return ret

    def remove_node(self, node=None, force=False):
        ret = None
        if isinstance(node, etree._Element):
            if not force:
                raise ConfirmDeleteNodeError(node)
            node.getparent().remove(node)
            ret = node

        return ret

    def get_available_networks(self, node=None, prefixlen=None):
        """
        Return list of available networks from a given node with subnet mask equal to prefixlen
        """
        pass
