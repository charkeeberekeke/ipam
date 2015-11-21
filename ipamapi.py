from flask import Flask, request, abort, jsonify, make_response, g
import redis
import json
import lxml
from ipam.schema import *
import ipam.domain as ipamdomain

app = Flask(__name__)
SCHEMA_NAME = "ipam:schema"


def init_db():
    if not hasattr(g, 'db'):
        g.db = redis.StrictRedis(host="localhost", port=6379, db=0)
    return g.db

def init_schema():
    #    if not hasattr(g, 'db'):
    #    g.db = redis.StrictRedis(host="localhost", port=6379, db=0)

    #schema = Schema(redisdb=g.db, schema_name=SCHEMA_NAME)
    schema = Schema(redisdb=init_db(), schema_name=SCHEMA_NAME)
    return schema

#need to add authentication/authorization to the method
@app.route("/ipam/api/v1.0/schema/<schema_name>", methods=["GET"])
def get_schema(schema_name):
    schema = init_schema()
    try:
        ret = schema.get_groups(schema_name)
    except Exception, e:
        abort(400)
    return jsonify({schema_name : ret})

@app.route("/ipam/api/v1.0/schema/<schema_name>", methods=["DELETE"])
def delete_schema(schema_name):
    schema = init_schema()
    try:
        ret = schema.delete_domain(schema_name)
    except:
        abort(400)
    return jsonify({schema_name : ret})

#need to add authentication/authorization to the method
@app.route("/ipam/api/v1.0/schema/<schema_name>", methods=["POST"])
def new_schema(schema_name):
    """
    Format is a dict in json format, with schema name as key and groups list as value
    """
    schema = init_schema()
    try:
        schema.new_domain(schema_name)
        schema.update_domain(schema_name, request.json.get(schema_name))
        #schema.update_domain(schema_name, request.form[schema_name])
    except DomainAlreadyExistsError as e:
        abort(400) # issue informative 404 page 
    except InvalidGroupError as e:
        pass
    except Exception as e:
        pass

    return jsonify(request.json)

def del_schema(schema_name):
    pass

#need to add authentication/authorization to the method
@app.route("/ipam/api/v1.0/domain/<domain_name>", methods=["GET"])
def get_domain(domain_name):
    db = init_db()
    dom = db.get("ipam:domain:%s" % domain_name)
    if dom is None:
        abort(404)
    return dom 

#need to add authentication/authorization to the method
@app.route("/ipam/api/v1.0/domain/<domain_name>", methods=["POST"])
def new_domain(domain_name):
    """
    Format is json with 2 fields:
    schema : name
    xml : xml representation of domain structure
    """
    db = init_db()
    schema = init_schema()
    if request.content_type != "application/xml":
        abort(400)
    schema = Schema(json_str=db.get(SCHEMA_NAME))
    dom = ipamdomain.Domain(raw_xml=request.data, schema=schema)
    dom.save_to_db(db)
    return jsonify({"domain" : str(dom)})


@app.route("/ipam/api/v1.0/domain/<domain_name>/node", methods=["GET", "POST", "DELETE"])
def node_domain(domain_name):
    db = init_db()
    dom_xml = db.get("ipam:domain:%s" % domain_name)
    schema = init_schema()
#    schema = Schema(json_str=db.get(SCHEMA_NAME))
#    dom = ipamdomain.Domain(raw_xml=request.data, schema=schema)
    dom = ipamdomain.Domain(raw_xml=dom_xml, schema=schema)
    node_args = ["node_type", "name", "network"]
    if request.method == "GET":
        # arg are type, name and network
        kwargs = {k:v for (k,v) in request.args.iteritems() if k in node_args}
        ret = dom.get_node(**kwargs)
        #print lxml.etree.tostring(ret[0])
    elif request.method == "POST":
        ret = json.loads(request.data)
        pass
    elif request.method == "DELETE":
        ret = json.loads(request.data)
        pass
    #print ret
    ret_str = ""
    for r in ret:
        ret_str += lxml.etree.tostring(r)
        ret_str += "\n"
#    return lxml.etree.tostring(ret[0])
    return ret_str
#    return str(ret)


@app.route("/ipam/api/v1.0/domain/<domain_name>/network", methods=["GET"])
def network_domain(domain_name):
    pass

@app.route("/ipam/api/v1.0/domain/<domain_name>", methods=["DELETE"])
def del_domain(domain_name):
    db = init_db()
    dom_key = "ipam:domain:%s" % domain_name
    dom_xml = db.get(dom_key)
    db.delete(dom_key)
    return dom_xml

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
    # check if redis is running
    db = redis.StrictRedis(host="localhost", port=6379, db=0)
    SCHEMA_NAME = "ipam:schema"
    schema = Schema(redisdb=db, schema_name=SCHEMA_NAME)
    app.run(debug=True)
