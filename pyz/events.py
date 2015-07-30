
from pyz import log

class Event(object):
    """
    A class representing an abstract event
    to be resolved one step at a time.

    Does nothing when dead, but should be removed.
    """

    def __init__(self, stdscr, grid, coord):
        self.screen = stdscr
        self.grid = grid
        self.coord = coord

        self.dead = False

    def step(self):
        if self.dead:
            return

class GenericInteractVisualEvent(Event):

    def __init__(self, stdscr, grid, coord):
        Event.__init__(self, stdscr, grid, coord)

        self.ticks = 2

        self.step() # initialize visual effect so it takes effect THIS turn

    @log.logwrap
    def step(self):
        if self.dead:
            return

        node = self.grid.nodes[self.coord]
        if self.ticks == 2:
            node.reverse_video = True
        elif self.ticks == 1:
            node.reverse_video = False
        else:
            self.dead = True

        self.ticks -= 1
