import json

class DomainAlreadyExistsError(Exception):
    pass

class DomainDoesNotExistError(Exception):
    pass

class InvalidGroupError(Exception):
    pass

class InvalidDomainError(Exception):
    pass

class Schema:
    """
    Container class for schema file for domains
    """
    def __init__(self, file=None, json_str=""):
        """
        Open schema file containing domain definitions
        """
        self.file = file
        self.json_str = json_str
        self.domains = {}
        if json_str:
            try:
                self.domains = json.loads(self.json_str)
            except:
                pass
        elif self.file:
            try:
                self.domains = self.file and json.load(open(self.file)) or {}
            except IOError as e:
                pass

    def new_domain(self, domain):
        """
        Create new domain
        """
        if domain in self.domains:
            raise DomainAlreadyExistsError
        self.domains[domain] = []

    def get_domains(self):
        return self.domains.keys()

    def get_groups(self, domain):
        try:
            return self.domains[domain]
        except KeyError as e:
            raise DomainDoesNotExistError
        return self.domains.keys()
                                                                                                                          
    def update_domain(self, domain, groups):
        try:
            if not isinstance(groups, list):
                raise InvalidGroupError
            # must also test list to only have unique elements
            self.domains[domain] = groups
        except KeyError:
            raise DomainDoesNotExistError                                                                                                                             
    def save(self):
        try:
            json.dump(self.domains, open(self.file, "w"))
        except IOError:
            raise

    def load(self, domain):
        if isinstance(domain, dict):
            self.domains = domain
            for k in domain.values():
                if not isinstance(k, list):
                    raise InvalidGroupError
        else:
            raise InvalidDomainError

        self.domains = domain
