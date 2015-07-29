
import random

from pyz.curses_prep import curses

from pyz import audio
from pyz import gameworld
from pyz.vision import shell_tools
from pyz.vision.trees import fasttree

####################################
# GLOBALS

RADIUS = 16 # doesn't include center
DIMENSIONS = 2
X = 80 # X * 2 - 1 == screen width
Y = 50

PLAY = 1

BLOCK_CHANCE_MIN = 20
BLOCK_CHANCE_MAX = 80

####################################

class Event(object):
    """
    A class representing an abstract event
    to be resolved one step at a time.
    """

    def __init__(self, stdscr, grid, coord):
        self.screen = stdscr
        self.grid = grid
        self.coord = coord

    def step(self):
        pass

####################################

def establish_colors(bg=curses.COLOR_BLACK):
    curses.init_pair(1, curses.COLOR_WHITE, bg) # W/B

    # grass
    curses.init_pair(2, 2, bg) # G/B
    curses.init_pair(3, 10, bg) # G!/B

    # player
    curses.init_pair(4, 11, bg) # Y!/B

    # tree
    curses.init_pair(5, 58, bg) # Brown/B

    # smoke
    curses.init_pair(6, 8, bg) # Gray/B

    # clay
    curses.init_pair(7, 88, bg) # Maroon/B
    # curses.init_pair(8, 88, bg) # Maroon/Brown

def mainwrapped(stdscr):

    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    establish_colors()

    stdscr.bkgd(' ', curses.color_pair(1)) # set background color to WHITE ON BLACK

    stdscr.addstr(0, 0, "Starting...")
    stdscr.refresh()

    if PLAY:

        stdscr.addstr(1, 0, "Loading viewtree...")
        stdscr.refresh()
        # PLAYER_VIEW = viewtree.gen_view_from_radius(RADIUS)
        # (PLAYER_VIEW, angle_table_2D) = fasttree.gen_new(RADIUS, DIMENSIONS)
        PLAYER_VIEW = fasttree.VIEW

        # make trees
        blocked = set()

        if PLAY == 1:
            for _ in xrange(random.randint(BLOCK_CHANCE_MIN, BLOCK_CHANCE_MAX)):
                (x,y) = (random.randint(0,X-2), random.randint(0,Y-2))
                blocked.add((x,y))
                # blocked.add((x,y+1))
                # blocked.add((x+1,y))
                # blocked.add((x+1,y+1))

        elif PLAY == 2:
            blocked = set([(20,20)])

        # grid
        stdscr.addstr(2, 0, "Creating game grid...")
        stdscr.refresh()
        GRID = gameworld.Grid2D(X,Y, PLAYER_VIEW, blocked)

        if PLAY == 1:
            rad3 = shell_tools.shell_coords(0, 3)
            rad7 = shell_tools.shell_coords(0, 7)

            # smoke
            (cx, cy) = (37, 15)
            GRID.nodes[(cx,cy)].set_smoke()
            GRID.blocked.add( (cx,cy) )
            for x,y in rad3:
                GRID.blocked.add( (x+cx, y+cy) )
                GRID.nodes[(x+cx, y+cy)].set_smoke()

            # grass
            (cx, cy) = (20, 9)
            if not (cx,cy) in blocked:
                GRID.nodes[(cx,cy)].set_grass()
            for x,y in rad7:
                if not (x+cx,y+cy) in blocked:
                    GRID.nodes[(x+cx, y+cy)].set_grass()

        try:
            stdscr.addstr(3, 0, "Playing...")
            stdscr.refresh()
            # audio.play("/Users/Matt/Music/iTunes/iTunes Media/Music/Alt-J/This Is All Yours/05 Left Hand Free.m4a")
            audio.rough_loop("environment/swamp.aif", 100)
            GRID.play(stdscr)
        except Exception as e:
            print e

    audio.stop_all_sounds()
    curses.curs_set(1)

    print "\n"*(Y + 10)


def main():
    curses.wrapper(mainwrapped)


if __name__ == '__main__':
    # printsl(u'\u2588'*100)
    main()
