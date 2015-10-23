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

    def __init__(self, controlmanager):
        self.controlmanager = controlmanager
        self.controlmanager.add_controller(self)

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
