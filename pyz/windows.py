
from pyz import curses_prep


def make_panel(h,l, y,x, box=True):
    """
    SOURCE:  http://stackoverflow.com/questions/21172087/i-need-an-example-of-overlapping-curses-windows-using-panels-in-python
    """
    win = curses_prep.curses.newwin(h,l, y,x)
    win.erase()
    if box:
        win.box()

    panel = curses_prep.curses.panel.new_panel(win)

    return win, panel


class Renderable(object):

    def __init__(self, stdscr, position=(0,0)):
        self.stdscr = stdscr
        self.position = position
        (self.window, self.panel) = make_panel(10, 20, *position[::-1])
        # self.window.keypad(1)
        self.panel.hide()
        curses_prep.panel.update_panels()

    def move(self, position):
        self.position = position # X/Y
        self.panel.move(*position[::-1]) # Y/X
        curses_prep.panel.update_panels()

    def render(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()

        self.window.border()
        self.window.addstr(0, 0, "TESTING")
        self.window.refresh()

        # self.window.clear()
        # self.panel.hide()
        # curses_prep.panel.update_panels()
        # curses.doupdate()
