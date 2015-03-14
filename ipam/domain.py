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
        try:
            net = IPv4Network(ip)
        except:
            return None
        else:
            return net

    def _is_subnet(self, supernet, net):
        """
        Tests if net is subnet of supernet.
        Does the native test in IPv4Address as well as ensure net prefix is longer than supernet
        """
        _super = IPv4Network(supernet)
        _net = IPv4Network(net)
        return (_net in _super) and (_net.prefixlen > _super.prefixlen)

    def add_node(self, node_type=None, parent=None, name="", network=None):
        """
        Add node into the tree. Node type must conform to the schema.
        Return element represeting the node
        """
        child = None
        network = self._validated_ip(network) and network or "0.0.0.0/0"

        if name and node_type in self.groups:
            if (isinstance(parent, etree._Element) and (self.groups.index(node_type) == self.groups.index(parent.tag) + 1) 
                    and self._is_subnet(parent.get("network"), network)):
                # add another condition in that the child network must be a subnet of the parent network
                child = etree.Element(node_type, name=name, network=network)
                parent.append(child)
            elif parent is None and (self.groups.index(node_type) == 0):
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

        return node
        
    def set_node(self, node=None, **kwargs):
        """
        Change given node according to new properties set in kwargs
        """
        pass

    def get_available_networks(self, node=None, prefixlen=None):
        """
        Return list of available networks from a given node with subnet mask equal to prefixlen
        """
        pass
