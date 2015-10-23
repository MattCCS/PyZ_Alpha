"""
"""

# standard
import abc

####################################

class Controller(object):
    """
    Class which is given input and rendered in no particular order.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def interact(self, key):
        """
        Handle the given key code -- can be None!
        """
        pass

    @abc.abstractmethod
    def render(self, stdscr):
        """
        Renders self to the given screen -- as
        best as possible -- without erroring.
        """
        pass
