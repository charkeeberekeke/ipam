from flask import Flask, request, abort, jsonify, make_response
import redis
from ipam.schema import *
import ipam.domain as ipamdomain

db = redis.StrictRedis(host="localhost", port=6379, db=0)
app = Flask(__name__)
SCHEMA_NAME = "ipam:schema"


#need to add authentication/authorization to the method
@app.route("/ipam/api/v1.0/domain/<domain_name>", methods=["GET"])
def get_domain(domain_name):
    dom = db.get("ipam:domain:%s" % domain_name)
    if dom is None:
        abort(404)
    return dom 

#need to add authentication/authorization to the method
@app.route("/ipam/api/v1.0/schema/<schema_name>", methods=["GET"])
def get_schema(schema_name):
    schema = Schema(json_str=db.get(SCHEMA_NAME))
    try:
        ret = schema.get_groups(schema_name)
    except Exception, e:
        print e
    return jsonify({schema_name : ret})

#need to add authentication/authorization to the method
@app.route("/ipam/api/v1.0/domain/<domain_name>", methods=["POST"])
def new_domain(domain_name):
    """
    Format is json with 2 fields:
    schema : name
    xml : xml representation of domain structure
    """
    if request.content_type != "application/xml":
        abort(400)
    schema = Schema(json_str=db.get(SCHEMA_NAME))
    dom = ipamdomain.Domain(raw_xml=request.data, schema=schema)
    dom.save_to_db(db)
    return jsonify({"domain" : str(dom)})

#need to add authentication/authorization to the method
@app.route("/ipam/api/v1.0/schema/<schema_name>", methods=["POST"])
def new_schema(schema_name):
    """
    Format is a dict in json format, with schema name as key and groups list as value
    """
    if not request.json or not schema_name in request.json or not isinstance(request.json.get(schema_name), list):
        abort(400)
    try:
        schema = Schema(json_str=db.get(SCHEMA_NAME))
        print schema.domains
        schema.new_domain(schema_name)
        schema.update_domain(schema_name, request.json.get(schema_name))
    except Exception as e:
        abort(400)

    db.set(SCHEMA_NAME, json.dumps(schema.domains))
    return jsonify(request.json)

def del_domain(domain_name):
    pass

def del_schema(schema_name):
    pass


# node naming convention will be root>parent1>parent2>node or such format
# to facilitate easy searching using lxml
def add_node(domain, parent_node, network, name):
    pass

def set_node(domain, node, network=None, name=None):
    pass

def del_node(domain, node):
    pass

# ideally run this function clientside but will also make available in api
def get_available_network(domain, node):
    pass

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({"error" : "Not found"}))

if __name__ == "__main__":
    app.run(debug=True)
