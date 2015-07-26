import curses

def main(stdscr):
    curses.start_color()
    curses.use_default_colors()
    for bg in range(256):
        for i in range(0, curses.COLORS):
            curses.init_pair(i + 1, i, bg)
        try:
            for i in range(256):
                stdscr.addstr(str(i), curses.color_pair(i))
        except curses.error:
            # End of screen reached
            pass
        if stdscr.getch() == ord('q'):
            break
        stdscr.clear()

curses.wrapper(main)
