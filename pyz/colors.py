"""
This file contains mappings of {color names -> ASSIGNED curses indices}
"""

from pyz.curses_prep import curses

# ####################################
# # SETTING UP THE LOGGER
# import os
# from pyz import log
# ROOTPATH = os.path.splitext(__file__)[0]
# LOGPATH = "{0}.log".format(ROOTPATH)
# LOGGER = log.get(__name__, path=LOGPATH)
# LOGGER.info("----------BEGIN----------")

####################################
# updated dynamically when colors are requested

CURSES_COLORS = {
    "black"          :   0,
    "gray"           :   8,
    "white"          :   15,

    "dark red"       :   1,
    "dark green"     :   2,
    "dark yellow"    :   3,
    "dark blue"      :   4,
    "dark magenta"   :   5,
    "dark teal"      :   6,
    "dark white"     :   7,

    "red"            :   9,
    "green"          :   10,
    "yellow"         :   11,
    "blue"           :   12,
    "magenta"        :   13,
    "teal"           :   14,

    "brown"          :   58,
    "maroon"         :   88,
}

PRESET = {}
IDX = 2

####################################

def lookup(name):
    """Look up the name value in the color table"""
    return CURSES_COLORS[name]

def fg_bg_to_index(fg_name, bg_name="black"):
    """Creates the color pair and returns its index"""
    global PRESET, IDX

    key = (fg_name, bg_name)
    if key in PRESET:
        return PRESET[key]
    else:
        # LOGGER.debug("new pair: {} -- {}/{} {}/{}".format(IDX, fg_name, CURSES_COLORS[fg_name], bg_name, CURSES_COLORS[bg_name]))
        curses.init_pair(IDX, CURSES_COLORS[fg_name], CURSES_COLORS[bg_name])
        out = curses.color_pair(IDX)
        PRESET[key] = out
        IDX += 1
        return out
