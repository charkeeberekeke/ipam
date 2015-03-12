from lxml import etree
from schema import *

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
    Container class for domain object with a etree representation of xml structure of nodes and networks
    """

    def __init__(self, domain=None, schema=None, path_to_xml=None):
        """
        Initialize object with domain name. Class will open xml file with name 'domain.xml'. 
        If no file is present, set file object none
        and initialize tree structure
        """
        self.file = None
        self.domain = domain
        self.path_to_xml = path_to_xml

        if self.path_to_xml:
            self.file = os.path.join(self.path_to_xml, "%s.xml" % domain)
            try:
                # parse xml file and extract domain name from root element with tag domain
                # set self.domain to extracted domain as well as self.file as file
                # set self.root to tree root
                # exit __init__
            except IOError, XMLParsingError:
                pass

        if self.domain:
            self.root = etree.Element("domain", name=self.domain)
            if self.path_to_xml:
                self.file = os.path.join(self.path_to_xml, "%s.xml" % domain)
            else:
                # initialize etree on default location
        else:
            self.root = etree.Element("domain")


    def add_node(self, node_type=None, parent=None, name=None, network=None)
        """
        Add node into the tree. Node type must conform to the schema.
        Return element represeting the node
        """
        pass

    def get_node(self, node_type=None, name=None, network=None):
        """
        Return node with given properties 
        """
        pass

    def get_child_nodes(self, node_type=None, name=None):
        """
        Return list containing child nodes of given node
        """
        pass
    
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
