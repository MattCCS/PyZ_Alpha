#!/usr/bin/env python
# Author: Matthew Cotton

from pyz import settings
from pyz.curses_prep import curses, setup

from collections import OrderedDict

####################################

def say(s, r=400):
    import subprocess
    subprocess.check_output(['say', s, '-r', str(r)])

DEFAULT_COLOR = "white"
DEFAULT_MODE = curses.A_NORMAL

####################################

DIRECTIONAL_MAP_WSAD = {
    ord('w'): ( 0, -1),
    ord('s'): ( 0,  1),
    ord('a'): (-1,  0),
    ord('d'): ( 1,  0),
}

DIRECTIONAL_MAP_ARROW = {
    curses.KEY_UP    : ( 0, -1),
    curses.KEY_DOWN  : ( 0,  1),
    curses.KEY_LEFT  : (-1,  0),
    curses.KEY_RIGHT : ( 1,  0),
}

def get(name):
    return LayerManager.get(name)

####################################

class LayerManager(object):

    registry = {}

    def __init__(self, name, dims, wrap=False, restrict=False, sublayers=None):
        self.w, self.h = dims
        self.name = name

        if sublayers is None:
            sublayers = []

        self.restrict = restrict
        self.wrap = wrap
        self.points = {}
        self.layers = OrderedDict()     # string -> (x, y, layer) (ORDER MATTERS!)

        LayerManager.registry[name] = self

        for (x, y, each) in sublayers:
            self.add_layer(x, y, each)

    @staticmethod
    def get(name):
        return LayerManager.registry[name]

    ####################################
    # utilities
    def size(self):
        return (self.w, self.h)

    def convert_to_1d(self, x, y):
        return self.w * y + x

    def convert_to_2d(self, i):
        (y,x) = divmod(i, self.w)
        return (x,y)

    def out_of_bounds(self, x, y):
        return not (0 <= x < self.w) or not (0 <= y < self.h)

    def layer_out_of_bounds(self, x, y, layer):
        (w, h) = layer.size()
        return any([
            self.out_of_bounds(x,     y),
            self.out_of_bounds(x+w-1, y),
            self.out_of_bounds(x,     y+h-1),
            self.out_of_bounds(x+w-1, y+h-1),
            ])

    def reset(self):
        self.points = {}

    def reset_recursive(self):
        self.reset()
        for (_, _, layer) in list(self.layers.values()):
            layer.reset_recursive()

    ####################################
    # resizing

    def resize_diff(self, dw=0, dh=0):
        (w,h) = self.size()
        w += dw
        h += dh
        self.resize(w, h)

    def resize(self, w=0, h=0):
        (ow, oh) = self.size()

        self.w = w if w > 0 else ow
        self.h = h if h > 0 else oh

        self.on_resize()

    def on_resize(self):
        """
        Called on resize event

        Use for things like drawing borders
        """
        pass

    ####################################
    # setting points
    def set(self, x, y, char, color=None, mode=1):
        if type(char) is not int:
            assert len(char) == 1
        self.points[(x,y)] = (
            char,
            color if color is not None else DEFAULT_COLOR,
            mode if mode is not None else DEFAULT_MODE,
            )

    def unset(self, x, y):
        try:
            del self.points[(x,y)]
        except KeyError:
            pass

    ####################################
    # setting ranges
    def setlines(self, x, y, lines, color=None, mode=1):
        """
        For convenience, to allow blocks of text to be pre-written and split.
        """
        for (i,line) in enumerate(lines):
            self.setrange(x, y+i, line, color=color, mode=mode)

    def setrange(self, x, y, it, color=None, mode=1):
        for (i, c) in enumerate(it, x):
            # if not allow_beyond:
            #     if self.out_of_bounds(i, y):
            #         break
            self.set(i, y, c, color=color, mode=mode)

    ####################################
    # pre-paired ranges
    def setrange_paired(self, x, y, it):
        for (i, (c, color, mode)) in enumerate(it, x):
            # if not allow_beyond:
            #     if self.out_of_bounds(i, y):
            #         break
            self.set(i, y, c, color=color, mode=mode)

    ####################################
    # iterating over lines
    def yield_rows_with_none(self):
        for y in range(self.h):
            yield (self.points.get((x,y), None) for x in range(self.w))

    def items(self):

        # if wrap:
        #     for ((x,y),p) in self.points.iteritems():
        #         (x,y) = self.convert_to_2d(self.convert_to_1d(x,y))
        #         if self.out_of_bounds(x,y):
        #             continue # because iteritems has no order, we can't break :/
        #         yield (x, y, p)
        # else:
        for ((x,y),p) in self.points.items():
            yield (x, y, p)

    ####################################
    # manager operations
    def get_layer(self, name):
        return self.layers[name]

    def add_layer(self, x, y, layer):
        self.layers[layer.name] = (x,y,layer)

    def delete_layer(self, name):
        del self.layers[name]

    def move_layer(self, x, y, name):
        (_, _, layer) = self.get_layer(name)
        if self.restrict:
            if self.layer_out_of_bounds(x, y, layer):
                return False
        self.delete_layer(name)
        self.add_layer(x, y, layer)
        return True

    def move_layer_inc(self, x, y, name):
        (sx, sy, layer) = self.get_layer(name)
        x = sx + x
        y = sy + y
        return self.move_layer(x, y, name)

    ####################################
    # rendering
    def self_items(self):
        for ((x,y),p) in self.points.items():
            yield (x, y, p)

    def render_dict(self):
        points = {}

        # render sub-layers, in order
        for (ox, oy, layer) in list(self.layers.values()):
            for (x, y, point) in layer.render_to(ox, oy):
                if self.out_of_bounds(x,y):
                    continue
                points[(x,y)] = point

        # render self on top
        for (x, y, point) in self.self_items():
            if self.wrap:
                (x,y) = self.convert_to_2d(self.convert_to_1d(x,y))
            if self.out_of_bounds(x, y):
                continue
            points[(x,y)] = point

        return points

    def items(self, wrap=None):
        for ((x,y),p) in self.render_dict().items():
            yield (x, y, p)

    def render_to(self, ox, oy, wrap=None):
        for (x, y, point) in self.items(wrap=wrap):
            yield (x+ox, y+oy, point)

    ####################################
    # debug functions
    def debug_layers(self):
        for (name, (x,y,layer)) in list(self.layers.items()):
            print(("{}: pos={}/{} dims={}".format(name, x,y, layer.size())))

    def yield_rows_with_none(self):
        points = self.render_dict()
        for y in range(self.h):
            yield (points.get((x,y), None) for x in range(self.w))

    def debugrender(self, space=True):
        return '\n'.join((' ' if space else '').join((p[0] if p is not None else ' ') for p in row) for row in self.yield_rows_with_none())

####################################

# there will be, after initscr

CHARSETS = {
    "curses" : [],
    "ascii"  : '++++-|-|',
}

def set_curses_border():
    CHARSETS['curses'] = [
        curses.ACS_ULCORNER,
        curses.ACS_URCORNER,
        curses.ACS_LLCORNER,
        curses.ACS_LRCORNER,
        curses.ACS_HLINE,
        curses.ACS_VLINE,
        curses.ACS_HLINE,
        curses.ACS_VLINE,
    ]

def add_border(layer, charset='curses', chars=None, color=None):
    if chars:
        charset = chars
    else:
        charset = CHARSETS[charset]
    (x,y) = layer.size()
    tl, tr, bl, br, up, right, down, left = charset

    layer.setrange(0,   0, [tl]+[up]*(x-2)+[tr], color=color)
    layer.setrange(0, y-1, [bl]+[down]*(x-2)+[br], color=color)
    for oy in range(y-2):
        layer.set(  0, oy+1,  left, color=color)
        layer.set(x-1, oy+1, right, color=color)

####################################

def layer_test():

    # cursor
    A = LayerManager("a", (1,1))
    A.set(0,0,'X', mode=curses.A_STANDOUT)

    # container for cursor
    SM = LayerManager("container", (8,8), restrict=True, sublayers=[
            (0, 0, A),
        ])

    # test 1
    L1 = LayerManager("base", (3,8), wrap=True)
    L1.setrange(2, 0, "Here is a long string that i made for you")

    # test 2
    # L2 = LayerManager("top", (5,5))
    # L2.setrange(0,1, "AAAAAAAAAAAAAAAAA")

    # sub-window with border
    LM = LayerManager("subwin", (10,10), sublayers=[
            (1, 1, L1),
            # (1, 4, L2),
            (0, 0, gen_border("border1", 10,10)),
            (1, 1, SM),
        ])

    # main screen
    MAIN = LayerManager("main", (40,24), sublayers=[(30, 6, LM)])

    return MAIN


def curses_test_wrapped(stdscr):
    setup(stdscr)

    MAIN = layer_test()
    SM = LayerManager.get("container")
    L1 = LayerManager.get("base")

    code = (0,0)
    sub_code = (0,0)
    size_code = (0,0)
    main_code = (0,0)

    while True:

        if any(sub_code):
            (dx, dy) = sub_code
            SM.move_layer_inc(dx, dy, "a")
            sub_code = (0,0)
        if any(code):
            (dx, dy) = code
            MAIN.move_layer_inc(dx, dy, "subwin")
            code = (0,0)
        if any(size_code):
            (dx, dy) = size_code
            L1.resize_diff(dx, dy)
            size_code = (0,0)
        if any(main_code):
            (dx, dy) = main_code
            MAIN.resize_diff(dx, dy)
            main_code = (0,0)

        for (x, y, (c, color, mode)) in list(MAIN.items()):
            try:
                stdscr.addstr(y, x*2, c, mode)
                pass
            except curses.error:
                break
        (x, y, _) = SM.get_layer("a")
        stdscr.addstr(20,0, "x/y: {}/{}".format(x, y), 1)
        (x, y, _) = MAIN.get_layer("subwin")
        stdscr.addstr(21,0, "wx/wy: {}/{}".format(x, y), 1)
        (w, h) = L1.size()
        stdscr.addstr(22,0, "w/h: {}/{}".format(w, h), 1)

        stdscr.refresh()
        key = stdscr.getch()
        if key == ord('q'):
            break

        if key in DIRECTIONAL_MAP_ARROW:
            sub_code = DIRECTIONAL_MAP_ARROW[key]

        elif key in DIRECTIONAL_MAP_WSAD:
            code = DIRECTIONAL_MAP_WSAD[key]

        elif key == ord('u'):
            size_code = (0, -1)
        elif key == ord('j'):
            size_code = (0, 1)
        elif key == ord('h'):
            size_code = (-1, 0)
        elif key == ord('k'):
            size_code = (1, 0)

        elif key == ord('['):
            main_code = (0, -1)
        elif key == ord(']'):
            main_code = (0, 1)
        elif key == ord('-'):
            main_code = (-1, 0)
        elif key == ord('='):
            main_code = (1, 0)

        stdscr.clear()


def curses_test():
    curses.wrapper(curses_test_wrapped)
    # curses_test_wrapped(None)


BODY = """\
 /-\\ 
 \\_/ 
 -o-
/ | \\
  o
 / \\
 | |""".split('\n')


if __name__ == '__main__':
    # speedtest()
    # LM = layer_test()

    curses_test()
