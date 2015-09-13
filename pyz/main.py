
# standard
import random

# project
from pyz import curses_prep
from pyz.gamedata import json_parser
from pyz import audio
from pyz import gameworld
from pyz.vision.trees import fasttree
from pyz import colors

####################################
# GLOBALS

RADIUS = 16 # TODO:  doesn't include center (?)
DIMENSIONS = 2
X = 80 # X * 2 - 1 == screen width
Y = 50

####################################

def mainwrapped(stdscr):
    curses_prep.setup(stdscr)

    stdscr.addstr(0, 0, "Starting...")
    stdscr.refresh()

    stdscr.addstr(1, 0, "Loading viewtree...")
    stdscr.refresh()

    # grid
    stdscr.addstr(2, 0, "Creating game grid...")
    stdscr.refresh()
    GRID = gameworld.Grid2D(stdscr, X, Y)

    try:
        stdscr.addstr(3, 0, "Playing...")
        stdscr.refresh()
        # audio.play("/Users/Matt/Music/iTunes/iTunes Media/Music/Alt-J/This Is All Yours/05 Left Hand Free.m4a")
        audio.rough_loop("environment/swamp.aif", 100)
        GRID.play()
    except Exception as e:
        print(e)

    audio.stop_all_sounds()
    curses_prep.curses.curs_set(1)

    print(("\n"*(Y + 10)))

def main():
    json_parser.load_all()
    curses_prep.curses.wrapper(mainwrapped)


if __name__ == '__main__':
    main()
