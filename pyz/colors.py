"""
This file contains mappings of {color names -> ASSIGNED curses indices}
"""

def lookup(name):
    """Look up the name value in the color table"""
    return COLORTABLE[name]

COLORTABLE = {
    "white":        1,
    "dark green":   2,
    "green":        3,
    "yellow":       4,
    "brown":        5,
    "gray":         6,
    "maroon":       7,
}
