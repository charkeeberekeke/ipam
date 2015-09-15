import time

from lxml import etree
from schema import *
from ipaddr import IPv4Address, IPv4Network
import redis

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

    def __init__(self, domain=None, groups=None, xml_file=None, raw_xml="", schema=None, schema_name=""):
#    def __init__(self, domain=None, schema=None, xml_file=None, raw_xml=""):
        """
        Initialize object with domain name. Class will open xml file with name 'domain.xml'. 
        If no file is present, set file object none
        and initialize tree structure
        """
        self.xml_file = xml_file
        self.raw_xml = raw_xml
        self.domain = domain
        self.groups = groups and groups[:] or []
        self.groups.insert(0, "domain")
        self.root = None
        self.timestamp = str(int(time.time()))
        self.version = 1
        self.schema_name = schema_name
        self.schema = schema

        if self.raw_xml:
            self.root = etree.fromstring(raw_xml)
            self.domain = self.root.text
            self.version = int(self.root.get("data-version"))
            self.timestamp = self.root.get("data-timestamp")
            self.schema_name = self.root.get("data-schema")
            self.groups = self.schema and self.groups.extend(self.schema.get_groups(self.schema_name)) or self.groups
        elif self.xml_file:
            # will throw IOError for invalid xml_file, to be caught by Domain caller
            self.root = etree.parse(self.xml_file).getroot()
            self.domain = self.root.text
            self.version = int(self.root.get("data-version"))
            self.timestamp = self.root.get("data-timestamp")
            self.schema_name = self.root.get("data-schema")
            self.groups = self.schema and self.groups.extend(self.schema.get_groups(self.schema_name)) or self.groups
        elif self.domain:
            #self.root = etree.Element("div", data-timestamp=self.timestamp, data-version=str(self.version), data-schema=self.schema_name)
            self.root = etree.Element("div", **{ "data-timestamp" : self.timestamp, 
                "data-version" : str(self.version), "data-schema" : self.schema_name  })
            self.root.text = self.domain
        else:
            self.root = etree.Element("div", **{ "data-schema" : schema_name })

        self.root.set("data-network", "0.0.0.0/0")
        self.root.set("class", "domain")

    def validate(self, node=None):
        """
        Validate entire domain tree according to add_node validation checks
        """
        #node = (node is not None) and node or self.root
        if node is None:
            node = self.root

        get_children = lambda x: (isinstance(x, etree._Element) and x.tag in ["li", "div"] and len(x) == 1 and x[0].tag == "ul") \
                    and x[0].getchildren() or []

        for n in get_children(node): 
            index = node[0].index(n)
            node[0].remove(n)
            ret = self.add_node(parent=node, name=n.text,
                    network=n.get("data-network"), node_type=n.get("class"), validate_only=True)
            if ret is not None: 
                if len(n) != 0:
                    if not self.validate(node=n):
                        node[0].insert(index, n)
                        return False
            else:
                node[0].insert(index, n)
                return False

            node[0].insert(index, n)

        return True

    def __repr__(self):
        return "%s:%s" % (self.domain, self.version)

    def _validated_ip(self, ip):
        """
        Validates IP address argument
        Accepts ip address in string format, raises InvalidIPError exception if IP is invalid
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

    def version(self):
        return self.version

    def timestamp(self):
        return self.timestamp

    def xml(self):
        #        return etree.tostring(self.root, pretty_print=True)
        return etree.tostring(self.root)

    def save(self, xml_file=None):
        """
        Save etree xml to designated file
        """
        # add logic in performing write only if data was changed
        self.version += 1
        self.timestamp = str(int(time.time()))
        self.root.set("version", str(self.version))
        self.root.set("timestamp", self.timestamp)
        xml = etree.tostring(self.root, pretty_print=True, xml_declaration=True, encoding="UTF-8")
        with open(xml_file, "w") as f:
            f.write(xml)

    def save_to_db(self, db=None):
        """
        Save to redis db
        Validate first if saved copy exists in redis and if saved version is more recent
        """
        if isinstance(db, redis.client.StrictRedis) and db.ping():
            name = "ipam:domain:%s" % self.domain
            tmp = db.get(name)
            if tmp is not None:
                tmp = Domain(raw_xml=tmp)
                if tmp.version() != self.version:
                    # raise exception about saved version not equal to new version
                    return False
                else:
                    self.version = str(int(self.version) + 1)
            self.timestamp = str(int(time.time()))
            self.root.set("version", str(self.version))
            self.root.set("timestamp", self.timestamp)
        #    xml = etree.tostring(self.root, pretty_print=True, xml_declaration=True, encoding="UTF-8")
            xml = etree.tostring(self.root)
            db.set(name, xml)
            return True

        return False

    def _is_subnet(self, supernet, net, raise_exception=True):
        """
        Tests if net is subnet of supernet.
        Does the native test in IPv4Address as well as ensure net prefix is longer than supernet
        Will raise exception if net is not a subnet of supernet by default, can be set to return False
        """
        #need to change default network, 0.0.0.0/0 introduces subtle issues
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

    def _is_unique_amongst_siblings(self, parent=None, **kwargs):
        """
        Determines whether provided name and network (non-overlapping) are unique among given parent's children nodes
        network parameter should already be validated by calling function add_node
        name comparision is case-insensitive
        """
        if not isinstance(parent, etree._Element):
            return False

        if parent.getchildren() == []:
            parent.append(etree.Element("ul"))
            return True

        for k, v in kwargs.items():
            condition = "test_%s" % k
            #test_name = lambda x: v.lower() == x.get(k).lower()
            test_name = lambda x: v.lower() == x.text.lower()
            test_network = lambda x: any([self._is_subnet(v, x.get("data-%s" % k), raise_exception=False),
                                        self._is_subnet(x.get("data-%s" % k), v, raise_exception=False),
                                        IPv4Network(v) == IPv4Network(x.get("data-%s" % k))])
            if condition in locals().keys():
                test = locals().get(condition)
                for s in parent[0]:
                    if test(s):
                        if k == "name":
                            raise DuplicateSiblingError("%s:%s" % (k, s.text))
                        else:
                            raise DuplicateSiblingError("%s:%s" % (k, s.get("data-%s" % k)))
                
        return True

    def _append_node(self, child, parent):
        if parent.getchildren() == []:
            parent.append(etree.Element("ul"))
        elif parent[0].tag == "ul":
            parent[0].append(child)

    def add_node(self, node_type=None, parent=None, name="", network="", validate_only=False):
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
            (1) parent is an etree element instance with tag set to li
            (2) node_type is direct descendant/child of parent node_type
            (3) network is a subnet of parent network
            (4) name/network is unique amongst siblings
            currently adding node with no parent works if parent is domain element.
            will change this such that domain is the first element of groups and that adding a node after parent requires
            setting parent paremeter to self.root
            """
            if (isinstance(parent, etree._Element) 
                    and parent.tag in ["li", "div"] 
                    and (self.groups.index(node_type) == self.groups.index(parent.get("class")) + 1) 
                    and self._is_subnet(parent.get("data-network"), network) 
                    and self._is_unique_amongst_siblings(name=name, network=network, parent=parent)):
                child = etree.Element("li")
                child.set("class", node_type)
                child.set("data-network", network)
                child.text = name
                if not validate_only:
                    self._append_node(child, parent)
            elif parent is None:
                if self.groups.index(node_type) != 1:
                    raise InvalidNodeTypeError(node_type)
                child = etree.Element("li")
                child.set("class", node_type)
                child.set("data-network", network)
                child.text = name
                if not validate_only:
                    self._append_node(child, self.root)

        return child

    def get_node(self, node_type=None, name=None, network=None):
        """
        Return node/s with given properties 
        """
        node = []
        if node_type and (node_type in self.groups):
            if name:
                #q = "//%s[@name='%s']" % (node_type, name)
                q = '//li[@class="%s" and contains(., "%s")]' % (node_type, name)
            else:
                q = '//li[@class="%s"]' % node_type
            node = self.root.xpath(q)
        elif network: # may need to improve the logic behind selection of name/nodetype vs network search
            pass

        return node

    def _search_network(self, network, node):
        """
        Return node for a given network
        """
        if node.tag not in ["li", "div"] or len(node) != 1 or node[0].tag != "ul":
            return node
        # If xml_tree integrity is guaranteed at this point, may bypass validation checks above
        # to speed up recursive search
        
        for c in node[0].getchildren():
            try:
                if self._is_subnet(c.get("data-network"), network):
                    node = self._search_network(network, c)
            except AssignedIPnotinSubnet:
                continue

        return node
        
    def set_node(self, node=None, validate_only=False, **kwargs):
        """
        Change given node according to new properties set in kwargs
        Node_type change not allowed
        Network change  will involve validation for ip address rules
        """
        ret = None

        # only allow changes to list <li> items at this time
        if not isinstance(node, etree._Element) and node.tag != "li":
            return ret

        parent = node.getparent().getparent() # check if a more efficient method using xpath can replace this
        if "network" in kwargs:
            if (not self._validated_ip(kwargs["network"]) 
                    or not self._is_subnet(parent.get("data-network"), kwargs["network"])):
                return ret
            if node.getchildren() != []:
                if any([ self._is_subnet(kwargs["network"], c.get("data-network")) is False for c in node[0].getchildren() ]):
                    return ret

        if not self._is_unique_amongst_siblings(parent=parent, **kwargs):
            return ret

        if "name" in kwargs:
            if not validate_only:
                node.text = kwargs["name"]
            ret = node
        if "network" in kwargs:
            if not validate_only:
                node.set("data-network", kwargs["network"])
            ret = node
#        if isinstance(node, etree._Element):
#            # add a case for changing root element attribute(s)
#            if "network" in kwargs and self._validated_ip(kwargs["network"]):
#                if len(node): 
#                    # if node has children, may need to research more reliable way of doing this
#                    for c in node.getchildren():
#                        if not self._is_subnet(kwargs["network"], c.get("network")):
#                            return ret
#                if self.groups.index(node.tag) and not self._is_subnet(node.getparent().get("network"), kwargs["network"]):
#                    # if node_type is not first in group and node is not subnet of parent node network
#                    return ret
#                if not self._is_unique_amongst_siblings(network=kwargs["network"], parent=node.getparent()):
#                    # figure out a way to run this once for network and name fields
#                    return ret
#                if not validate_only:
#                    node.set("network", kwargs["network"])
#                ret = node
#            if "name" in kwargs and self._is_unique_amongst_siblings(name=kwargs["name"], parent=node.getparent()):
#                if not validate_only:
#                    node.set("name", kwargs["name"])
#                ret = node

        return ret

    def remove_node(self, node=None, force=False):
        """
        Remove given node, will raise exception if force argument is set to False
        """
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
