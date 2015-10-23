"""
"""

# standard
import traceback

# custom
from pyz import audio
from pyz import layers
from pyz import gameworld
from pyz import curses_prep

####################################

class ControlManager(object):

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.pending_controllers = []
        self.controllers = [gameworld.GridManager2D(self)]

    def add_controller(self, controller):
        self.pending_controllers.append(controller)

    def loop(self):
        
        while True:
            if not self.controllers:
                break

            # render the controller stack
            for controller in self.controllers:
                controller.render(self.stdscr)

            # get input safely
            curses_prep.curses.flushinp()
            try:
                key = self.stdscr.getch()
            except KeyboardInterrupt:
                return # user quit!

            # guaranteed to exist by earlier line,
            # and guaranteed to be the topmost controller.
            dead = controller.interact(key)
            if dead:
                self.controllers.pop()

            # update controller stack
            self.controllers += self.pending_controllers
            self.pending_controllers = []

####################################

def mainwrapped(stdscr):
    curses_prep.setup(stdscr)
    layers.set_curses_border()
    stdscr.timeout(1000)

    stdscr.addstr(0, 0, "Starting...")
    stdscr.refresh()

    stdscr.addstr(1, 0, "Loading viewtree...")
    stdscr.refresh()

    # grid
    # stdscr.addstr(2, 0, "Creating game grid...")
    # stdscr.refresh()
    # GRID = gameworld.GridManager2D(stdscr, X, Y)

    # stdscr.addstr(3, 0, "Playing...")
    # stdscr.refresh()

    manager = ControlManager(stdscr)
    try:
        manager.loop()
    except Exception as e:
        with open("BAD2.txt", 'w') as f:
            f.write(traceback.format_exc())

    audio.stop_all_sounds()
    curses_prep.curses.curs_set(1)
