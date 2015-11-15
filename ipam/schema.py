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
    def __init__(self, file=None, json_str="", redisdb=None, schema_name=None):
        """
        Open schema file containing domain definitions
        """
        self.file = file
        self.json_str = json_str
        self.domains = {}
        self.redisdb = redisdb
        self.schema_name = schema_name
        if self.redisdb is not None and self.schema_name is not None:
            schema = redisdb.get(self.schema_name)
            try:
                if schema is None or not isinstance(json.loads(schema), dict):
                    self.redisdb.set(self.schema_name, "{}")
                    schema = "{}"
            except ValueError, e:
                print "ValueError"
                self.redisdb.set(self.schema_name, "{}")
                schema = "{}"
            self.domains = json.loads(schema)
        elif json_str:
            try:
                self.domains = json.loads(self.json_str)
            except:
                pass
        elif self.file:
            try:
                self.domains = self.file and json.load(open(self.file)) or {}
            except IOError as e:
                pass

    def update_redisdb(self):
        self.redisdb.set(self.schema_name, json.dumps(self.domains))

    def new_domain(self, domain):
        """
        Create new domain
        """
        if domain in self.domains:
            raise DomainAlreadyExistsError
        self.domains[domain] = []
        if self.redisdb:
            self.update_redisdb() 

    def get_domains(self):
        return self.domains.keys()

    def get_groups(self, domain):
        try:
            return self.domains[domain]
        except KeyError as e:
            #raise DomainDoesNotExistError
            return {}
        #return self.domains.keys()
                                                                                                                          
    def update_domain(self, domain, groups):
        try:
            if not isinstance(groups, list):
                raise InvalidGroupError
            # must also test list to only have unique elements
            self.domains[domain] = groups
            if self.redisdb:
                self.update_redisdb()
        except KeyError:
            raise DomainDoesNotExistError

    def delete_domain(self, domain):
        if domain in self.domains:
            tmp = self.domains[domain]
            del self.domains[domain]
            if self.redisdb:
                self.update_redisdb()
            return tmp
        else:
            return None

    def save(self):
        try:
            if self.redisdb:
                self.update_redisdb()
            elif self.file:
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
