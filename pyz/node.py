
import random

from pyz import audio
from pyz import data
from pyz import colors
from pyz.curses_prep import curses
from pyz.curses_prep import CODE


class Node2D(object):

    ERROR  = '!'

    def __init__(self, parentgrid, coord):

        self.parentgrid = parentgrid
        self.coord = coord

        self.reverse_video = False

        self.name = '---'
        self.passable = True
        self.transparent = True
        self.material = None
        self.appearance = None
        self.color = 0
        self.old_color = 0
        self.damageable = False
        self.health = 0
        self.objects = []
        self.set_dirt()

    ####################################
    # attribute assignment

    def set(self, name):
        data.reset(self, 'node', name)

    def set_tree(self):
        self.set('tree')

    def set_smoke(self):
        self.set('smoke')

    def set_grass(self):
        self.set('grass')

    def set_dirt(self):
        self.set('dirt')

    ####################################

    def damage(self, n):
        if self.damageable:
            self.health -= n
            if self.health <= 0:
                self.parentgrid.news.add("The {} dies.".format(self.name))
                self.die()

    def die(self):
        if self.name == 'tree':
            audio.play_random("foley/tree", volume=0.5)
        self.set_dirt()
        self.parentgrid.blocked.discard(self.coord)

    def render(self, layer, x, y):

        # yes, every tick
        if self.name == 'smoke':
            self.appearance = random.choice("%&")

        char = self.appearance if self.appearance else Node2D.ERROR

        try:
            if not self.reverse_video:
                layer.set(x, y, char.encode(CODE), color=colors.fg_bg_to_index(self.color))
            else:
                layer.set(x, y, char.encode(CODE), color=curses.A_REVERSE)
        except curses.error:
            pass # some out-of-bounds issue.
            # TODO: investigate!
