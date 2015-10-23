"""
"""

# standard
import abc

####################################

class AbstractWindow(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, layer):
        self._layer = layer

    @abc.abstractmethod
    def render(self):
        pass

####################################

class ControllingWindow(AbstractWindow):

    @abc.abstractmethod
    def interact(self, key):
        """Must return True when this window is done/dead."""
        pass
