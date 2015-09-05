# encoding: utf-8

import random
import time
import sys

from pyz.curses_prep import CODE
from pyz.curses_prep import curses
from pyz import colors

from pyz import audio
from pyz import player
from pyz import objects
from pyz import data
from pyz.vision.rays import arctracing
from pyz.vision import shell_tools
from pyz import utils
from pyz import layers

from pyz.terminal_size import true_terminal_size

####################################
# SETTING UP THE LOGGER
import os
from pyz import log # <3
ROOTPATH = os.path.splitext(__file__)[0]
LOGPATH = "{0}.log".format(ROOTPATH)
LOGGER = log.get(__name__, path=LOGPATH)
LOGGER.info("----------BEGIN----------")

####################################

if sys.version_info[0] == 2:
    BODY = """\
 /-\\ 
 \\_/ 
 -o-
/ | \\
  o
 / \\
 | |""".split('\n')
else:
    BODY = """\
 /⎺\\ 
 \\_/ 
 -o- 
⎛ | ⎞
  o  
 ⎛ ⎞ 
 ⎜ ⎟ """.split('\n')

####################################

BLOCK_CHANCE_MIN = 20
BLOCK_CHANCE_MAX = 80

RESERVED_X = 20
RESERVED_Y = 8

MIN_X = 20 + RESERVED_X
MIN_Y = 10 + RESERVED_Y

TOO_SMALL_MSG = [
    "RESIZE",
    "{} x {}".format(MIN_X, MIN_Y),
]

####################################

def relative_coords(coords, rel_coord):
    (rx, ry) = rel_coord
    return set([(x-rx, y-ry) for (x,y) in coords])

####################################

STANDING_DICT = {
    0: 'prone',
    1: 'crouching',
    2: 'standing',
}

SPEED_DICT = {
    0: 'sneaking',
    1: 'walking',   # 'normal'?
    2: 'sprinting', # 'frantic'?
}

ARROW_KEYS = {curses.KEY_LEFT, curses.KEY_RIGHT, curses.KEY_UP, curses.KEY_DOWN}

def say(s, r=400):
    import subprocess
    subprocess.check_output(['say', s, '-r', str(r)])

####################################

class Node2D(object):

    HIDDEN = '█'
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

####################################

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


# def yield_coords_offset(range_nums, offset_nums):
#     assert len(range_nums) == len(offset_nums)

#     for coord in yield_coords(range_nums):
#         yield tuple(map(sum, zip(coord, offset_nums)))

def key_to_coord(key):
    if key == curses.KEY_UP:
        return (0,1)
    elif key == curses.KEY_DOWN:
        return (0,-1)
    elif key == curses.KEY_LEFT:
        return (-1,0)
    elif key == curses.KEY_RIGHT:
        return (1,0)

    return (0,0)

####################################

class Grid2D:

    def __init__(self, stdscr, x, y):

        self.stdscr = stdscr

        self.spacing = 2
        
        self.x = x
        self.y = y
        self._truex = x
        self._truey = y

        self.nodes = {coord : Node2D(self, coord) for coord in yield_coords( (self.x, self.y) )}

        # make trees
        self.blocked = set()
        for _ in range(random.randint(BLOCK_CHANCE_MIN, BLOCK_CHANCE_MAX)):
            coord = (random.randint(0,x-2), random.randint(0,y-2))
            self.blocked.add(coord)
            self.nodes[coord].set_tree()

        self.visible = set()

        # events
        self.visual_events_top    = []
        self.visual_events_bottom = []
        self.requested_waits = []
        self.blocking_events      = []
        self.non_blocking_events  = []

        rad3 = shell_tools.shell_coords(0, 3)
        rad7 = shell_tools.shell_coords(0, 7)

        # smoke
        (cx, cy) = (37, 15)
        self.nodes[(cx,cy)].set_smoke()
        self.blocked.add( (cx,cy) )
        for x,y in rad3:
            self.blocked.add( (x+cx, y+cy) )
            self.nodes[(x+cx, y+cy)].set_smoke()

        # grass
        (cx, cy) = (20, 9)
        if not (cx,cy) in self.blocked:
            self.nodes[(cx,cy)].set_grass()
        for x,y in rad7:
            if not (x+cx,y+cy) in self.blocked:
                self.nodes[(x+cx, y+cy)].set_grass()

        # player and lantern
        self.player = player.Player()
        self.player.weapon = objects.WEAPONS['axe1']
        self.player_sneakwalksprint = 1
        self.player_stand_state = 2
        self.player.lantern = objects.Lantern(16, self.player)
        self.player.lantern.can_age = True
        self.player.flashlight = objects.Flashlight(24, 90, 15, self.player)

        lantern_coord = (17,9)
        self.lightsources = [self.player.flashlight, objects.Lantern(8, None, lantern_coord)]
        self.nodes[lantern_coord].set_dirt()
        self.nodes[lantern_coord].appearance = 'X'
        self.nodes[lantern_coord].color = "yellow"
        self.nodes[lantern_coord].old_color = "yellow"

    # def reset(self, coords=None):
    #     if coords is None:
    #         nodes = self.nodes.itervalues()
    #     else:
    #         nodes = (self.nodes[coord] for coord in coords)

    #     for node in nodes:
    #         node.reset()

    def frame_coords_2D(self, width, height):
        (px, py) = self.player.position()

        for y in range(py-height//2, py+height//2+1):
            yield [(x,y) for x in range(px-width//2, px+width//2+1)]

    def x_to_screen(self, x, px, width, BORDER_OFFSET_X=1, spacing=2):
        return x*spacing - px*spacing + width//2 # + BORDER_OFFSET_X

    def y_to_screen(self, y, py, height, BORDER_OFFSET_Y=1):
        return height//2 - y + py # - BORDER_OFFSET_Y - 1

    def xy_to_screen(self, coord, ppos, width, height, spacing=2, BORDER_OFFSET_X=1, BORDER_OFFSET_Y=1):
        (x,y) = coord
        (px,py) = ppos
        fx = self.x_to_screen(x, px, width, BORDER_OFFSET_X=BORDER_OFFSET_X, spacing=spacing)
        fy = self.y_to_screen(y, py, height, BORDER_OFFSET_Y=BORDER_OFFSET_Y)
        return (fx, fy)

    def render_grid(self, visible):

        layer = layers.LayerManager.get("gameworld")

        (px,py) = self.player.position()

        (w,h) = layer.size()

        for row in self.frame_coords_2D(w,h):

            for (x,y) in row:

                fx = self.x_to_screen(x, px, w, spacing=self.spacing)
                fy = self.y_to_screen(y, py, h)

                if not (x, y) in self.nodes:
                    layer.set(fx, fy, u'█'.encode(CODE), color=colors.fg_bg_to_index("white"), is_unicode=True)
                    # pass
                elif not (x-px, y-py) in visible:
                    # TODO: what does this do?
                    # X/Y are REAL coords (non-relative)
                    # so to check for visibility, we have to relativize them
                    pass
                else:
                    try:
                        self.nodes[(x,y)].render(layer, fx, fy)
                        # self.nodes[(x+self.x/2,y+self.y/2)].render(stdscr, x*2, y)
                    except KeyError:
                        pass # node out of bounds

    @log.logwrap
    def handle_interaction(self, key):

        ####################################
        # updating
        (oldx, oldy) = self.player.position()
        if key in ARROW_KEYS:

            (x,y) = self.player.position()
            if key == curses.KEY_UP:
                y = min(y+1, self.y-1)
            elif key == curses.KEY_DOWN:
                y = max(y-1, 0)
            elif key == curses.KEY_LEFT:
                x = max(x-1, 0)
            elif key == curses.KEY_RIGHT:
                x = min(x+1, self.x-1)

            if (x,y) == self.player.position():
                pass # edge of map
                # TODO: should be edge of AVAILABLE map
            elif self.nodes[(x,y)].passable:
                audio.play_movement(self.player_stand_state, self.player_sneakwalksprint, self.nodes[(x,y)].material)
                self.player.set_position( (x,y) )
            else:
                # it's an obstacle!  AKA gameobject
                if self.player.prefs.auto_attack and self.player.weapon:
                    self.player.weapon.attack_NODE(self.nodes[(x,y)], self, self.stdscr, (x,y))

        elif key in list(map(ord, 'sS')):
            # toggle sneak/walk/sprint
            self.player_sneakwalksprint = (self.player_sneakwalksprint + 1) % 3
            audio.play('weapons/trigger.aif', volume=0.2)
        elif key in list(map(ord, 'zZ')):
            # lower
            if self.player_stand_state > 0:
                self.player_stand_state -= 1
                if self.player_stand_state == 0:
                    audio.play('movement/changing/prone.aif')
                else:
                    audio.play('movement/changing/nonprone.aif')
        elif key in list(map(ord, 'xX')):
            # raise
            if self.player_stand_state < 2:
                self.player_stand_state += 1
                audio.play('movement/changing/nonprone.aif')

        if hasattr(self.player, 'flashlight'):
            if key == ord('f'):
                # toggle flashlight
                self.player.flashlight.toggle()
                time.sleep(0.2)

            elif key == ord('m'):
                self.player.flashlight.toggle_mode()

            self.player.flashlight.update_direction(key_to_coord(key))

    def determine_visible(self):

        ####################################
        # rendering

        # all light sources individually
        visible = set().union(*(utils.visible_coords_absolute_2D(self.blocked, light, light.position()) for light in self.lightsources))

        ####################################
        # RELATIVE

        # add special overlaps (trees the player *can't* see but which block vision nonetheless)
        # faster now, since 'visible' is smaller
        visible = utils.remaining(
            relative_coords(visible,      self.player.position()),
            relative_coords(self.blocked, self.player.position()),
            arctracing.BLOCKTABLE
            )

        # if we're in smoke, show adjacents
        if visible == set( [(0,0)] ):
            visible.update( [(1,0), (-1,0), (0,-1), (0,1)] )

        self.visible = visible

        # self.visible = 
        # U illuminated(rel) - blocked(rel)
        # - blocked(player)

    def has_visual_events(self):
        return bool(self.visual_events_top) or bool(self.visual_events_bottom)

    def visual_requested_wait(self):
        if self.requested_waits:
            wait = max(self.requested_waits)
            self.requested_waits = []
        else:
            wait = 0

        return wait

    @log.logwrap
    def tick(self, key):
        if self.window_too_small():
            return

        ####################################
        # TOP visual events pause interaction
        # since these are to be watched
        # BOTTOM visual events simply occur

        if not self.visual_events_top:
            self.handle_interaction(key)

        for obj in objects.GameObject.record:
            obj.age(self, self.stdscr)


    def render_player(self):
        layer = layers.LayerManager.get("gameworld")

        p = self.player.position()
        # say('player is at {} {}'.format(*p))
        if (0,0) in self.visible:
            (fx,fy) = self.xy_to_screen(p, p, *layer.size())
            # say('player set {} {}'.format(fx, fy))
            layer.set(fx, fy, 'P', color=colors.fg_bg_to_index("yellow"))


    def window_too_small(self):
        return self._truex < MIN_X or self._truey < MIN_Y

    def render_too_small(self):
        MAIN = layers.LayerManager.get("main")
        MAIN.reset_recursive() # TODO: <---

        for (y,row) in enumerate(TOO_SMALL_MSG):
            for (x,c) in enumerate(row):
                MAIN.set(x, y, c, color=colors.fg_bg_to_index("white"))


    def update_viewport(self, sound=True):
        flag = self.window_too_small()
        self._truex, self._truey = true_terminal_size()
        # ^ reserved
        curses.resize_term(self._truey, self._truex)
        self.resize_layers()
        if sound:
            audio.play("weapons/trigger.aif", volume=0.2)
        if flag != self.window_too_small():
            self.render_frame()

    def resize_layers(self):
        STATS_W = 15
        PLAYER_H = 11
        NEWS_H = 4

        MAIN = layers.get("main")
        MAIN.resize(self._truex-1, self._truey) # TODO: <---
        (w,h) = MAIN.size()
        STATS_H = h-1-1-PLAYER_H
        GAMEFRAME_W = w-1-1-STATS_W
        GAMEFRAME_H = h-1-1-NEWS_H

        layers.get("gameframe").resize(GAMEFRAME_W, GAMEFRAME_H)
        layers.get("gameworld").resize(GAMEFRAME_W-1-1, GAMEFRAME_H-1-1)

        layers.get("stats").resize(STATS_W, STATS_H)
        MAIN.move_layer(w-1-STATS_W, 1, "stats")

        layers.get("player").resize(STATS_W, PLAYER_H)
        MAIN.move_layer(w-1-STATS_W, 1+STATS_H, "player")

        layers.get("news").resize(GAMEFRAME_W, 4)
        MAIN.move_layer(1, 1+GAMEFRAME_H, "news")

    def render_frame(self):
        if self.window_too_small():
            self.render_too_small()
            return

        # RENDERING
        # layers.LayerManager.get("main").reset()
        # layers.LayerManager.get("gameworld").reset()
        layers.get("main").reset_recursive()
        
        ####################################
        # META-RENDERING

        # modifiers
        # TODO:
        # for event in self.visual_events_bottom:
        #     event.step()
        # self.visual_events_bottom = [event for event in self.visual_events_bottom if not event.dead]

        # background
        self.determine_visible()
        self.render_grid(self.visible)

        # player
        self.render_player()

        # exceptions
        # TODO:
        # for event in self.visual_events_top:
        #     event.step()
        # self.visual_events_top = [event for event in self.visual_events_top if not event.dead]

        # foreground
        # TODO:
        # if not (self._truex, self._truey) == true_terminal_size():
        #     print '\a'


    # def render(self):
    #     """
    #     TICKS visual events!
    #     """

    #     self.render_frame()

    #     while self.has_visual_events():

    #         time.sleep(self.visual_requested_wait())

    #         self.stdscr.erase()

    #         self.render_frame() # this *must* decrement all visual events.



    def render_GUI(self):
        if not self.window_too_small():
            layers.add_border(layers.get("main"), color=colors.fg_bg_to_index("white"))
            layers.get("main").setrange(0,0, "<main>", color=colors.fg_bg_to_index("white"))

            layers.get("gameworld").setrange(0, 0, "<gameworld>", color=colors.fg_bg_to_index("white"))

            layers.add_border(layers.get("gameframe"), color=colors.fg_bg_to_index("white"))
            layers.get("gameframe").setrange(0, 0, "<gameframe>", color=colors.fg_bg_to_index("white"))

            layers.add_border(layers.get("stats"), color=colors.fg_bg_to_index("white"))
            layers.get("stats").setrange(0, 0, "<stats>", color=colors.fg_bg_to_index("white"))

            layers.add_border(layers.get("player"), color=colors.fg_bg_to_index("white"))
            layers.get("player").setrange(0, 0, "<player>", color=colors.fg_bg_to_index("white"))
            layers.get("player").setlines(5, 2, BODY, color=colors.fg_bg_to_index("white"))

            layers.add_border(layers.get("news"), color=colors.fg_bg_to_index("white"))
            layers.get("news").setrange(0, 0, "<news>", color=colors.fg_bg_to_index("white"))


    def playwrap(self):

        # print "Playing..."

        MAIN = layers.LayerManager("main", (80,24),
            sublayers=[
                # (0, 0, layers.LayerManager("main_border", (80, 24))),
                (1, 1, layers.LayerManager("gameframe", (5,5), sublayers=[
                    (1, 1, layers.LayerManager("gameworld", (5,5))),
                ])),
                (63, 1, layers.LayerManager("stats", (5, 5))),
                (63, 13, layers.LayerManager("player", (5, 5))),
                (1, 19, layers.LayerManager("news", (5, 5))),
            ])

        self.update_viewport(sound=False)
        self.tick('')  # start
        self.render_frame()
        self.render_GUI()
        render_to(MAIN, self.stdscr)

        try:
            while True:
                # input
                curses.flushinp()
                key = self.stdscr.getch()

                if key == 113: # q
                    break

                if key == curses.KEY_RESIZE:
                    self.update_viewport()
                    continue

                # tick
                self.tick(key)

                # render
                self.render_frame()
                self.render_GUI()
                render_to(MAIN, self.stdscr)
        except KeyboardInterrupt:
            print("User quit.")

        print("Quit.")

    def play(self):
        try:
            self.playwrap()
        except Exception as e:
            import traceback
            say(str(e), r=200)
            with open("BAD.txt", 'w') as f:
                f.write(traceback.format_exc())


def render_to(main_layer, stdscr):
    stdscr.erase()

    for (x, y, (char, color, _)) in list(main_layer.items()):
        try:
            stdscr.addstr(y, x, char, color)
        except curses.error:
            break

    stdscr.refresh()
