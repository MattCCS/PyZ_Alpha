
# project
from pyz import curses_prep
from pyz.gamedata import json_parser
from pyz import controlmanager

####################################

def main():
    json_parser.load_all()
    curses_prep.curses.wrapper(controlmanager.mainwrapped)


if __name__ == '__main__':
    main()
