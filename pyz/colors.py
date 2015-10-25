"""
This file contains mappings of {color names -> ASSIGNED curses indices}
"""

from pyz import iterm_color_table
from pyz.curses_prep import curses

####################################
# color tables

FG_BG_PAIRS = {}

# must be pre-defined!
# TODO:  load from JSON?
NAME_TO_RGB = {
    "black"          :   (  0,  0,  0),

    "dark red"       :   (128,  0,  0),
    "dark green"     :   (  0,128,  0),
    "dark blue"      :   (  0,  0,128),
    "dark yellow"    :   (128,128,  0),
    "dark magenta"   :   (128,  0,128),
    "dark teal"      :   (  0,128,128),
    "gray"           :   (128,128,128),

    "dark white"     :   (192,192,192),

    "red"            :   (255,  0,  0),
    "green"          :   (  0,255,  0),
    "blue"           :   (  0,  0,255),
    "yellow"         :   (255,255,  0),
    "magenta"        :   (255,  0,255),
    "teal"           :   (  0,255,255),
    "white"          :   (255,255,255),

    "brown"          :   ( 95,  95, 0),
    "maroon"         :   (135,  0,  0),
}

PAIR_INDEX = 2
COLOR_INDEX = 2

FACTOR_255_TO_1000 = 1000.0 / 255.0

####################################

def get(fg, bg="black"):
    global PAIR_INDEX

    fg_rgb = coerce_to_rgb(fg) # allow RGB or name
    bg_rgb = coerce_to_rgb(bg) # coerce to RGB

    key = (fg_rgb, bg_rgb)

    if key in FG_BG_PAIRS:
        return FG_BG_PAIRS[key]
    else:
        # create new color pair
        fg_i = iterm_color_table.lookup(fg_rgb)
        bg_i = iterm_color_table.lookup(bg_rgb)

        curses.init_pair(PAIR_INDEX, fg_i, bg_i)
        out = curses.color_pair(PAIR_INDEX)
        FG_BG_PAIRS[key] = out
        PAIR_INDEX += 1
        return out

def coerce_to_rgb(name_or_rgb):
    if type(name_or_rgb) is not tuple:
        return NAME_TO_RGB[name_or_rgb]
    else:
        return name_or_rgb
