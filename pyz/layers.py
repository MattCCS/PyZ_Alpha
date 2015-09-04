#!/usr/bin/env python
# Author: Matthew Cotton

from pyz import settings
from pyz import curses_prep

from collections import OrderedDict

####################################

DEFAULT_COLOR = "white"
DEFAULT_MODE = curses_prep.curses.A_NORMAL

####################################

DIRECTIONAL_MAP_WSAD = {
    ord('w'): ( 0, -1),
    ord('s'): ( 0,  1),
    ord('a'): (-1,  0),
    ord('d'): ( 1,  0),
}

DIRECTIONAL_MAP_ARROW = {
    curses_prep.curses.KEY_UP    : ( 0, -1),
    curses_prep.curses.KEY_DOWN  : ( 0,  1),
    curses_prep.curses.KEY_LEFT  : (-1,  0),
    curses_prep.curses.KEY_RIGHT : ( 1,  0),
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
        for (_, _, layer) in self.layers.values():
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
    def set(self, x, y, char, color=None, mode=1, is_unicode=False):
        """None is transparent"""
        if not is_unicode:
            assert char is None or len(char) == 1
        self.points[(x,y)] = (
            char,
            color if color is not None else DEFAULT_COLOR,
            mode if mode is not None else DEFAULT_MODE,
            )

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
        for y in xrange(self.h):
            yield (self.points.get((x,y), None) for x in xrange(self.w))

    def items(self):

        # if wrap:
        #     for ((x,y),p) in self.points.iteritems():
        #         (x,y) = self.convert_to_2d(self.convert_to_1d(x,y))
        #         if self.out_of_bounds(x,y):
        #             continue # because iteritems has no order, we can't break :/
        #         yield (x, y, p)
        # else:
        for ((x,y),p) in self.points.iteritems():
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
        for ((x,y),p) in self.points.iteritems():
            yield (x, y, p)

    def render_dict(self):
        points = {}

        # render sub-layers, in order
        for (ox, oy, layer) in self.layers.values():
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
        for ((x,y),p) in self.render_dict().iteritems():
            yield (x, y, p)

    def render_to(self, ox, oy, wrap=None):
        for (x, y, point) in self.items(wrap=wrap):
            yield (x+ox, y+oy, point)

    ####################################
    # debug functions
    def debug_layers(self):
        for (name, (x,y,layer)) in self.layers.items():
            print "{}: pos={}/{} dims={}".format(name, x,y, layer.size())

    def yield_rows_with_none(self):
        points = self.render_dict()
        for y in xrange(self.h):
            yield (points.get((x,y), None) for x in xrange(self.w))

    def debugrender(self, space=True):
        return '\n'.join((' ' if space else '').join((p[0] if p is not None else ' ') for p in row) for row in self.yield_rows_with_none())

####################################

def add_border(layer, chars='++++-|-|', color=None):
    (x,y) = layer.size()
    tl, tr, bl, br, up, right, down, left = chars

    layer.setrange(0,   0, '{}{}{}'.format(tl,   up*(x-2), tr), color=color)
    layer.setrange(0, y-1, '{}{}{}'.format(bl, down*(x-2), br), color=color)
    for oy in xrange(y-2):
        layer.set(  0, oy+1,  left, color=color)
        layer.set(x-1, oy+1, right, color=color)

####################################

def layer_test():

    # cursor
    A = LayerManager("a", (1,1))
    A.set(0,0,'X', mode=curses_prep.curses.A_STANDOUT)

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
    curses_prep.setup(stdscr)

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

        for (x, y, (c, color, mode)) in MAIN.items():
            try:
                stdscr.addstr(y, x*2, c, mode)
                pass
            except curses_prep.curses.error:
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
    curses_prep.curses.wrapper(curses_test_wrapped)
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
    # print LM.debugrender()
    # print LM.debug_layers()

    curses_test()
