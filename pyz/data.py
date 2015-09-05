
import random

from pyz import colors
from pyz import log

####################################

ATTRIBUTES  = {}
PARAMETERS  = {}
OBJECTS     = {}
OTHER       = {}

####################################

def reset(obj, cat, name):
    """
    Set the default fields of the given object to those of the given name.

    ex:  set('grass', obj)
    """
    OBJECTS[name].set(obj)

class DataObject(object):
    """
    Represents the stored default data for an object or node.
    """

    def __init__(self, name, data):
        self.name = name
        self.__dict__.update(data)
        OBJECTS[self.name] = self

    def set(self, obj):
        """
        Sets the default fields of this DataObject onto the given object.
        """

        for attr in list(ATTRIBUTES.keys()):
            setattr(obj, attr, False)
        for (key, val) in list(vars(self).items()):
            setattr(obj, key, val)
        if "colors" in vars(self):
            # obj.color = colors.lookup(random.choice(self.colors))
            obj.color = random.choice(self.colors)
            obj.old_color = obj.color
        if "appearances" in vars(self):
            obj.appearance = random.choice(self.appearances)

    def __getattr__(self, key):
        """Sexy."""

        # DO error if asked for missing field:
        if not key in vars(self) and key in ATTRIBUTES:
            return False
        else:
            return vars(self)[key]

        # DO NOT error if asked for missing field:
        # if not key in self.__dict__:
        #     if key in ATTRIBUTES:
        #         return False
        #     else:
        #         raise AttributeError()
        # else:
        #     return self.__dict__[key]
