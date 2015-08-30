
import random

from pyz.curses_prep import curses

from pyz.gamedata import json_parser
from pyz import audio
from pyz import gameworld
from pyz.vision.trees import fasttree
from pyz import colors

from pyz import log # <3

####################################
# GLOBALS

RADIUS = 16 # TODO:  doesn't include center (?)
DIMENSIONS = 2
X = 80 # X * 2 - 1 == screen width
Y = 50

BLOCK_CHANCE_MIN = 20
BLOCK_CHANCE_MAX = 80

####################################

@log.logwrap
def mainwrapped(stdscr):

    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    # establish_colors()

    stdscr.bkgd(' ', curses.color_pair(1)) # set background color to WHITE ON BLACK

    stdscr.addstr(0, 0, "Starting...")
    stdscr.refresh()

    stdscr.addstr(1, 0, "Loading viewtree...")
    stdscr.refresh()
    # PLAYER_VIEW = viewtree.gen_view_from_radius(RADIUS)
    # (PLAYER_VIEW, angle_table_2D) = fasttree.gen_new(RADIUS, DIMENSIONS)

    # make trees
    blocked = set()
    for _ in xrange(random.randint(BLOCK_CHANCE_MIN, BLOCK_CHANCE_MAX)):
        (x,y) = (random.randint(0,X-2), random.randint(0,Y-2))
        blocked.add((x,y))
        # blocked.add((x,y+1))
        # blocked.add((x+1,y))
        # blocked.add((x+1,y+1))

    # grid
    stdscr.addstr(2, 0, "Creating game grid...")
    stdscr.refresh()
    GRID = gameworld.Grid2D(stdscr, X, Y, blocked)

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

@log.logwrap
def main():
    json_parser.load_all()
    curses.wrapper(mainwrapped)


if __name__ == '__main__':
    # printsl(u'\u2588'*100)
    main()
