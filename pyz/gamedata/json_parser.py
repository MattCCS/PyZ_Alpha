
import json
import os

from pyz import settings
from pyz import data
from pyz.gamedata import validation

####################################

DEBUG = False

def printdebug(s):
    if DEBUG:
        print s

DEFAULT_INDICATOR = "*"
ATTRIBUTES_INDICATOR = "attributes"

PARAM_EXCEPTIONS = ["spawns"]   # <---<<< these are ignored -- equiv. to commenting the JSON

####################################

def load_attributes():
    attributes = json.loads(open(settings.ATTRIBUTES_PATH).read())
    for (_, attr) in attributes.items():
        # ... name ...
        validation.validate_attribute(attr) # <3
    data.ATTRIBUTES.update(attributes)

def load_parameters():
    parameters = json.loads(open(settings.PARAMETERS_PATH).read())

    for (name, param) in parameters.items():
        # ... name ...
        assert name not in data.ATTRIBUTES
        validation.validate_parameter(param) # <3
        # param['fields'] = [validation.VALID_FIELDS[s] for s in param['fields']]

    data.PARAMETERS.update(parameters)

def load_order():
    return open(settings.LOAD_ORDER).read().strip().split('\n')

####################################

def validate_and_save_objects(objects):
    defaults = objects.get(DEFAULT_INDICATOR, {})
    objects.pop(DEFAULT_INDICATOR, None)

    for (obj_name, obj) in objects.items():
        printdebug('-'*20)
        printdebug("ON/O: {}/{}".format(obj_name, obj))
        for (param, val) in obj.items():
            printdebug("PARAM/VAL: {}/{}".format(param, val))
            if param in PARAM_EXCEPTIONS:
                printdebug("*IGNORING*")
                continue
            if param == ATTRIBUTES_INDICATOR:
                continue

            valmap = data.PARAMETERS[param]['fields']
            printdebug(valmap)
            if len(valmap) > 1:
                for (v,vm) in zip(val, valmap):
                    validation.validate_as(v, vm)
            else:
                validation.validate_as(val, valmap[0])

        if ATTRIBUTES_INDICATOR in obj:
            for attr in obj[ATTRIBUTES_INDICATOR]:
                assert attr in data.ATTRIBUTES
                obj[attr] = True
            del obj[ATTRIBUTES_INDICATOR]

        data.DataObject(obj_name, obj)

def validate_and_save_nodes(nodes):
    defaults = nodes.get(DEFAULT_INDICATOR, {})
    nodes.pop(DEFAULT_INDICATOR, None)

    for (node_name, node) in nodes.items():
        printdebug('-'*20)
        printdebug("NN/N: {}/{}".format(node_name, node))
        for (param, val) in node.items():
            printdebug("PARAM/VAL: {}/{}".format(param, val))
            if param in PARAM_EXCEPTIONS:
                printdebug("*IGNORING*")
                continue

            if param == ATTRIBUTES_INDICATOR:
                continue

            valmap = data.PARAMETERS[param]['fields']
            printdebug(valmap)
            if len(valmap) > 1:
                for (v,vm) in zip(val, valmap):
                    validation.validate_as(v, vm)
            else:
                validation.validate_as(val, valmap[0])

        if ATTRIBUTES_INDICATOR in node:
            for attr in node[ATTRIBUTES_INDICATOR]:
                assert attr in data.ATTRIBUTES
                node[attr] = True
            del node[ATTRIBUTES_INDICATOR]

        data.DataObject(node_name, node)

####################################

def load_path(path):
    files = [f for f in os.listdir(settings.absolutize_gamedata(path)) if not f.startswith('.')]
    return files

def load_file(path):
    path = settings.absolutize_gamedata(path)
    return json.loads(open(path).read())

def load(path):
    # TODO:
    """
    NODES ARE NOT VALIDATED!
    """
    key = path.rstrip(os.path.sep)

    if path.endswith(os.path.sep):
        files = load_path(key)
        for filename in files:
            print "... Loading {}...".format(filename)
            validate_and_save_objects(load_file(os.path.join(path, filename)))
    elif path.endswith('nodes'):
        node_data = load_file(path + '.json')
        validate_and_save_nodes(node_data)
    else:
        data.OTHER[key].update(load_file(path + '.json'))

def load_all():
    print "Loading attributes..."
    load_attributes()

    print "Loading parameters..."
    load_parameters()

    print "Loading load order..."
    rest = load_order()
    for each in rest:
        print "Loading {}...".format(each)
        load(each)

if __name__ == '__main__':
    load_all()
