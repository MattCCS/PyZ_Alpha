import curses

def main(stdscr):
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(7, 10, 0)

    stdscr.addstr("test", curses.color_pair(7))

    stdscr.getch()

curses.wrapper(main)
