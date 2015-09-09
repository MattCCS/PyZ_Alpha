
import time
import random

from pyz import audio
from pyz import data
from pyz import colors
from pyz import objects
from pyz.curses_prep import curses
from pyz.curses_prep import CODE


class Node2D(object):

    ERROR  = '!'

    def __init__(self, parentgrid, coord):

        self.parentgrid = parentgrid
        self.coord = coord

        self.reverse_video = False

        self.name = '---'
        self.material = None
        self.appearance = None
        self.color = 0
        self.old_color = 0
        self.damageable = False
        self.health = 0
        self.objects = []
        self._object_render_last_tick = 0
        self._object_render_threshold = 0.8
        self._object_render_index = 0 # always mod, in case this number has changed
        self.set("dirt")

    def position(self):
        return self.coord

    def is_passable(self):
        return not any(obj.impassible for obj in self.objects)

    ####################################
    # attribute assignment

    def set(self, name):
        data.reset(self, 'node', name)

    def add(self, name):
        self.objects.append(objects.make(name, self))

    ####################################

    def render(self, layer, x, y):

        # base stuff
        char = self.appearance if self.appearance else Node2D.ERROR
        color = self.color

        # object stuff
        # TODO: NOTE: this forces objects to have an appearance!
        if self.objects:
            t = time.time() # TODO:  just save one value to the class.

            if abs(t - self._object_render_last_tick) > self._object_render_threshold:
                self._object_render_last_tick = t
                self._object_render_index += 1

            self._object_render_index %= len(self.objects)

            obj = self.objects[self._object_render_index]
            char = obj.appearance
            color = obj.color

        # gas/smoke stuff
        # ...

        color = colors.fg_bg_to_index(color)
        if self.reverse_video:
            color = curses.A_REVERSE

        # actual settings
        layer.set(x, y, char.encode(CODE), color=color)
