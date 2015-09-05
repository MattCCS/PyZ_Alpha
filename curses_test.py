import curses

def main(stdscr):
    curses.start_color()
    curses.use_default_colors()

    for bg in range(256):
        for i in range(0, curses.COLORS):
            curses.init_pair(i + 1, i, bg)
        try:
            for i in range(256):
                c = str(i)
                c = curses.ACS_ULCORNER
                # c = u'\u239e'.encode("utf-8")
                # c = u'\u0438'.encode('utf-8')
                # stdscr.addstr(c, curses.color_pair(i))
                # stdscr.addch(9118)
                stdscr.addstr('\u239e')
        except curses.error:
            # End of screen reached
            pass
        if stdscr.getch() == ord('q'):
            break
        stdscr.clear()

curses.wrapper(main)
