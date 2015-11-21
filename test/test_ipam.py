#need to run the ipam api and programmatically call rest functions for testing
from nose.tools import ok_, eq_, raises, with_setup
import json

try:
    import ipamapi
except ImportError:
    sys.path.append(os.path.abspath(".."))
    import ipamapi

class TestIpam:
    def __init__(self):
#       ipamapi.app.run(debug=True)
        self.test_app = ipamapi.app.test_client()
#        pass
#    def setUp(self):
#        self.app = ipamapi.app.test_client()
        #ret = self.app.delete("/ipam/api/v1.0/schema/Test")

#    def test_delete(self):
#        ret = self.test_app.delete("/ipam/api/v1.0/schema/Test")
#        print ret
#        print ret.status
#        print type(ret)
#        ok_(ret.status == '200')
    
    def init_schema(self):
        return self.test_app.delete("/ipam/api/v1.0/schema/Test")

    def test_01_delete_init(self):
        ret = self.init_schema()
        ok_(ret.status_code == 200)

    def test_02_get(self):
        ret = self.test_app.get("/ipam/api/v1.0/schema/Test")
        #ok_(True)
        ret_data = json.loads(ret.data)
        ok_(ret_data["Test"] == {})

    def test_03_post(self):
        post = {'Test': ['Galaxy', 'Solar System', 'Planet']}
        ret = self.test_app.post("/ipam/api/v1.0/schema/Test", 
                headers={"Content-Type" : "application/json"}, 
                data=json.dumps(post))
        ok_(ret.status_code == 200, "Post Status Code")
        ret_data = json.loads(ret.data)
        ok_(isinstance(ret_data, dict))
        ok_(ret_data["Test"] == post["Test"])
        
    def test_04_get_nonempty(self):
        ret = self.test_app.get("/ipam/api/v1.0/schema/Test")
        ret_data = json.loads(ret.data)
        ok_(ret_data["Test"] == ['Galaxy', 'Solar System', 'Planet'])

    def test_05_delete_nonempty(self):
        ret = self.init_schema()
        ret_data = json.loads(ret.data)
        ok_(ret_data["Test"] == ['Galaxy', 'Solar System', 'Planet'])

    def test_06_new_domain(self):
        schema = {'Test': ['Galaxy', 'Solar_System', 'Planet']}
        domain = """
        <domain name="Test8237492834" network="0.0.0.0/0" schema="Test">\n  <Galaxy name="Milky Way" network="10.0.0.0/12">\n
        <Solar_System name="Sun" network="10.0.0.0/19"/>\n    <Solar_System name="Betelguese" network="10.15.0.0/19"/>\n
        <Solar_System name="Sirius" network="10.14.0.0/16"/>\n    <Solar_System name="Polaris" network="10.1.0.0/19"/>\n  
        </Galaxy>\n  <Galaxy name="Andromeda" network="10.64.0.0/12"/>\n</domain>
        """
        ret = self.test_app.post("/ipam/api/v1.0/schema/Test", 
                headers={"Content-Type" : "application/json"}, 
                data=json.dumps(schema))
        ret = self.test_app.post("/ipam/api/v1.0/domain/Test8237492834",
                headers={"Content-Type" : "application/xml"},
                data=domain) 
        print ret.data
        ok_(ret.status_code == 200)

    def test_07_delete_domain(self):
        ret = self.test_app.delete("/ipam/api/v1.0/domain/Test8237492834")
        print ret.data
        ok_(ret.status_code == 200)
