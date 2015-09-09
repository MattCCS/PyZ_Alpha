"""
This file contains tools for meta-validation of game data.
"""

####################################
# SETTING UP THE LOGGER
import os
from pyz import log
ROOTPATH = os.path.splitext(__file__)[0]
LOGPATH = "{0}.log".format(ROOTPATH)
LOGGER = log.get(__name__, path=LOGPATH)
LOGGER.info("----------BEGIN----------")

####################################

def asserteq(a, b):
    try:
        assert a == b
    except AssertionError:
        LOGGER.critical("FAILED! {} != {}".format(repr(a), repr(b)))
        raise

def assertin(a, b):
    try:
        assert a in b
    except AssertionError:
        LOGGER.critical("FAILED! {} not in {}".format(repr(a), repr(b)))
        raise

####################################

def char(s):
    if len(s) == 1:
        return s
    else:
        raise ValueError

VALID_FIELDS = {
    "str"        : str,
    "int"        : int,
    "float"      : float,
    "char"       : char,
    "list[str]"  : lambda L: [ str(s) for s in L],
    "list[int]"  : lambda L: [ int(s) for s in L],
    "list[char]" : lambda L: [char(s) for s in L],
    # dicts...
}

def validate_as(data, typ):
    LOGGER.debug("Validating {} as {}".format(repr(data), repr(typ)))
    asserteq(data, VALID_FIELDS[typ](data))

def validate_attribute(attr):
    LOGGER.debug("Validating attr: {}".format(attr))
    asserteq(set(attr.keys()), set(['description']))
    validate_as(attr['description'], 'str')

def validate_parameter(param):
    LOGGER.debug("Validating param: {}".format(param))
    asserteq(set(param.keys()), set(['description', 'fields']))
    validate_as(param['description'], 'str')
    validate_as(param['fields'], 'list[str]')
    LOGGER.debug("Validating fields...")
    for field in param['fields']:
        assertin(field, VALID_FIELDS)
