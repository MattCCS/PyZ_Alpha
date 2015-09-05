

from __future__ import unicode_literals

import os
import sys
import random

# import smarttree
from pyz.line_drawing import fasttree
from pyz.line_drawing import raytracing2
from pyz.line_drawing import coord_gen_utils

from pyz import audio

####################################
# GLOBALS

PLAY = 1
GRAPH = 0

RADIUS = 36 # doesn't include center
DIMENSIONS = 2
X = 90 # X * 2 - 1 == screen width
Y = 50

# X = 175
# Y = 90

BLOCK_CHANCE_MIN = 20
BLOCK_CHANCE_MAX = 50

####################################

from pygetch import stdin
from pygetch.settings import settings


def tup2bin(tup):
    return int(''.join(map(str, tup)), 2)

def bin2tup(n):
    return tuple(map(int, bin(n)[2:]))


class Node2D:

    HIDDEN = '@'
    PLAYER = 'H'
    SOLID  = 'O'
    GLASS  = '/'
    SMOKE  = '%'
    AIR    = '.'
    ERROR  = '!'

    def __init__(self, code):
        # passable, transparent
        # 1 1 = air
        # 1 0 = fog/smoke
        # 0 1 = glass
        # 0 0 = solid

        if type(code) is int:
            code = bin2tup(code)

        self.passable, self.transparent = code
        # self.visible = False
        self.has_player = False

    def reset(self):
        # self.visible = False
        self.has_player = False

    def set_tree(self):
        self.passable = False
        self.transparent = False

    def set_smoke(self):
        self.passable = True
        self.transparent = False

    def code(self):
        return (self.passable, self.transparent)

    def code_num(self):
        return tup2bin(map(int, self.code()))

    def render(self):
        c = self.code_num()

        if self.has_player:
            return Node2D.PLAYER

        # if not self.visible:
        #     # return u'\u2588'  # UNICODE
        #     return Node2D.HIDDEN

        if c == 0:
            return Node2D.SOLID
        elif c == 1:
            return Node2D.GLASS
        elif c == 2:
            return Node2D.SMOKE
        elif c == 3:
            return Node2D.AIR
        else:
            return Node2D.ERROR


def yield_coords(range_nums):
    if not range_nums:
        yield tuple()
        return

    # we want to iterate like Z/Y/X <--- better solution?
    first = range_nums[0]
    rest  = range_nums[1:]

    for n in range(first):
        for coord in yield_coords(rest):
            yield (n,) + coord


def yield_coords_offset(range_nums, offset_nums):
    assert len(range_nums) == len(offset_nums)

    for coord in yield_coords(range_nums):
        yield tuple(map(sum, zip(coord, offset_nums)))


class Grid2D:

    def __init__(self, x, y, player_view, blocked_set):
        
        self.x = x
        self.y = y

        # # make plane
        # gen_row     = lambda n: [Node2D(3) for i in range(n)]
        # gen_plane   = lambda x,y: [gen_row(x) for i in range(y)]
        # self.nodes = gen_plane(x,y)
        self.nodes = {coord : Node2D(3) for coord in yield_coords( (self.x, self.y) )}

        print self.nodes

        self.blocked = blocked_set
        for coord in blocked_set:
            self.nodes[coord].set_tree()

        self.view = player_view
        self.player = (0,0)
        self.player_sneakwalksprint = 1
        self.player_stand_state = 2

    def reset(self, coords=None):
        if coords is None:
            nodes = self.nodes.itervalues()
        else:
            nodes = (self.nodes[coord] for coord in coords)

        for node in nodes:
            node.reset()

    def relative_blocked(self):
        (px,py) = self.player
        return set([(x-px, y-py) for (x,y) in self.blocked])

    def frame_coords_2D(self):
        # ABSOLUTE

        for y in range(self.y-1, 0-1, -1):
            yield [(x,y) for x in range(self.x)]

    def render(self, visible):

        (px,py) = self.player

        return ''.join(
                    ' '.join(
                        ( (Node2D.HIDDEN if not (x-px,y-py) in visible else self.nodes[(x,y)].render()) for (x,y) in row)
                        )
                for row in self.frame_coords_2D())

    # @profile
    def tick(self, key):

        ####################################
        # updating
        if tuple(map(ord, key)) in settings.ANSI_ARROW_KEYS:
            key = tuple(map(ord, key))
            if not key:
                raise RuntimeError()

            (x,y) = self.player
            if key == settings.KEYS['UP']:
                y = min(y+1, self.y-1)
            elif key == settings.KEYS['DOWN']:
                y = max(y-1, 0)
            elif key == settings.KEYS['LEFT']:
                x = max(x-1, 0)
            elif key == settings.KEYS['RIGHT']:
                x = min(x+1, self.x-1)

            if self.nodes[(x,y)].passable:
                audio.play_movement(self.player_stand_state, self.player_sneakwalksprint, 'dirt')
                self.player = (x,y)

        elif key in set('sS'):
            # toggle sneak/walk/sprint
            self.player_sneakwalksprint = (self.player_sneakwalksprint + 1) % 3
            audio.play('weapon/trigger.aif', volume=0.2)
        elif key in set('zZ'):
            # lower
            if self.player_stand_state > 0:
                self.player_stand_state -= 1
                if self.player_stand_state == 0:
                    audio.play('movement/changing/prone.aif')
                else:
                    audio.play('movement/changing/nonprone.aif')
        elif key in set('xX'):
            # raise
            if self.player_stand_state < 2:
                self.player_stand_state += 1
                audio.play('movement/changing/nonprone.aif')

        ####################################
        # rendering
        visible = self.view.visible_coords(self.relative_blocked())  # MUST PASS RELATIVE

        # if we're in smoke, show adjacents
        if visible == set( [(0,0)] ):
            visible.update( [(1,0), (-1,0), (0,-1), (0,1)] )
            # visible.update(list(product([-1,0,1], repeat=2)))

        (px,py) = self.player

        # # blockers
        # for (x,y) in blocked:
        #     try:
        #         self.nodes[y][x].visible = True
        #     except IndexError:
        #         # print (x,y)
        #         raise # outside map

        # visible
        # for (x,y) in visible:
        #     if x+px < 0 or y+py < 0:
        #         continue

        #     try:
        #         self.nodes[(x+px, y+py)].visible = True
        #     except IndexError:
        #         pass # outside map

        # player
        self.nodes[self.player].has_player = True
        # self.reset(self.last_updated ^ visible) # woah.

        # rendered_nodes = [[N.render() for N in row] for row in reversed(self.nodes)]
        # rendered_nodes = [(Node2D.HIDDEN if not coord in visible else self.nodes[coord].render()) for coord in self.frame_coords_2D()]
        # rendered_nodes = ((Node2D.HIDDEN if not coord in visible else self.nodes[coord].render()) for )

        # print rendered_nodes

        # render_buffer = render_to_buffer(rendered_nodes)
        # print repr(render_buffer)
        # printsl(''.join(rendered_nodes))
        printsl(self.render(visible))

        ####################################
        # reset

        # reset --> offset???

        # self.reset(self.last_updated - visible)
        self.reset() # <--- improve this


    def play(self):

        print "Playing..."

        self.tick('')  # start

        while True:

            # input
            key = stdin.getch()
            if key == settings.CONTROL_C:
                break

            # tick
            self.tick(key)

        print "Quit."



def printsl(s):
    sys.stdout.write(s.encode('utf-8'))
    sys.stdout.flush()

def s_and_back(s):
    return s + '\b'*max(len(s)-1, 0) + '\r'

def render_to_buffer(array2d):
    s = ''.join('{:<80}'.format(' '.join(row)) for row in array2d)
    return s_and_back(s)


def main():
    # print list(yield_coords((3,10)))
    # return

    if PLAY:

        # PLAYER_VIEW = viewtree.gen_view_from_radius(RADIUS)
        PLAYER_VIEW = fasttree.gen_new(RADIUS, DIMENSIONS)

        # make trees
        blocked = set()

        if PLAY == 1:
            for _ in range(random.randint(BLOCK_CHANCE_MIN, BLOCK_CHANCE_MAX)):
                (x,y) = (random.randint(0,X-2), random.randint(0,Y-2))
                blocked.add((x,y))
                # blocked.add((x,y+1))
                # blocked.add((x+1,y))
                # blocked.add((x+1,y+1))

        elif PLAY == 2:
            blocked = set([(20,20)])

        print len(PLAYER_VIEW.visible_coords(blocked))

        # grid
        GRID = Grid2D(X,Y, PLAYER_VIEW, blocked)

        if PLAY == 1:
            # smoke
            smoke = coord_gen_utils.shell_coords(0, 3)

            GRID.nodes[(37,15)].set_smoke()
            GRID.blocked.add( (37,15) )
            for x,y in smoke:
                GRID.blocked.add( (x+37, y+15) )
                GRID.nodes[(x+37, y+15)].set_smoke()

        os.system("stty -echo") # <--- oh my god, that's literally it.  that disables all echoing.
        os.system('tput civis')
        try:
            GRID.play()
        except Exception as e:
            print e
        os.system("stty echo")
        os.system('tput cnorm')


    if GRAPH:
        ####################################
        from mpl_toolkits.mplot3d import Axes3D # IMPORTANT
        import matplotlib.pyplot as plt

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        # S = coord_gen_utils.shell_coords(60,64, dimensions=2) # <---<<<
        # S = raytracing2.gen_path_bounded_absolute((0,0), (50,-37))
        S = coord_gen_utils.all_paths_to_points(coord_gen_utils.shell_wrap(32), listify=True)
        S = [e for l in S for e in l]
        print S
        ax.scatter(*zip(*S), c='r', marker='o')

        plt.show()

    print "\n"*(Y + 10)

if __name__ == '__main__':
    # printsl(u'\u2588'*100)
    main()
