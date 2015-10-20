# encoding: utf-8

import random
import time
import sys

from pyz.curses_prep import CODE
from pyz.curses_prep import curses
from pyz import colors

from pyz.windows.news import NEWS
from pyz.windows import stats_window
from pyz import audio
from pyz import player
from pyz import objects
from pyz.vision.rays import arctracing
from pyz.vision import shell_tools
from pyz.vision import utils
from pyz import layers

from pyz import grid2d
from pyz.grid2d import GRID

from pyz.terminal_size import true_terminal_size

####################################

PYTHON2 = sys.version_info[0] == 2

if PYTHON2:
    BODY = u"""\
 /-\\ 
 \\_/ 
 -o-
/ | \\
  o
 / \\
 | |""".split('\n')
else:
    BODY = u"""\
 /⎺\\ 
 \\_/ 
 -o- 
⎛ | ⎞
  o  
 ⎛ ⎞ 
 ⎜ ⎟ """.split('\n')

BORDER_BLOCK = u'█'

####################################

BLOCK_CHANCE_MIN = 50
BLOCK_CHANCE_MAX = 50

RESERVED_X = 20
RESERVED_Y = 8

# these should be determined dynamically...
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

####################################

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


class GridManager2D(object):

    def __init__(self, stdscr, x, y):

        self.MAIN = layers.LayerManager("main", (80,24),
            sublayers=[
                # (0, 0, layers.LayerManager("main_border", (80, 24))),
                (1, 1, layers.LayerManager("gameframe", (5,5), sublayers=[
                    (1, 1, layers.LayerManager("gameworld", (5,5))),
                ])),
                (63, 1, layers.LayerManager("stats", (5, 5))),
                (63, 13, layers.LayerManager("player", (5, 5))),
                (1, 19, layers.LayerManager("news", (5, 5))),
            ])

        self.stdscr = stdscr
        self.stdscr.timeout(1000)
        self.stats = stats_window.StatsWindow(layers.get("stats"))

        self.spacing = 2

        self.x = x
        self.y = y
        self._truex = x
        self._truey = y

        for (_, node_obj) in GRID.nodes.items():
            node_obj.set("dirt")

        # make trees
        for _ in range(random.randint(BLOCK_CHANCE_MIN, BLOCK_CHANCE_MAX)):
            coord = (random.randint(0,x-2), random.randint(0,y-2))
            GRID.nodes[coord].add("tree")

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
        # (cx, cy) = (37, 15)
        # GRID.nodes[(cx,cy)].set_smoke()
        # self.blocked.add( (cx,cy) )
        # for x,y in rad3:
        #     self.blocked.add( (x+cx, y+cy) )
        #     GRID.nodes[(x+cx, y+cy)].set_smoke()

        # grass
        (cx, cy) = (20, 9)
        GRID.nodes[(cx,cy)].set("grass")
        for x,y in rad7:
            GRID.nodes[(x+cx, y+cy)].set("grass")

        (cx,cy) = (20,20)
        GRID.nodes[(cx,cy)].add("stone wall")
        for y in range(cy, cy+8+1):
            for x in range(cx, cx+8+1):
                pos = (x,y)
                if x not in [cx, cx+8] and y not in [cy, cy+8]:
                    continue
                if not GRID.nodes[pos].objects:
                    GRID.nodes[pos].add("stone wall")

        x1 = objects.GameObject()
        x1.name = 'ruby'
        x1.appearance = "*"
        x1.color = "red"

        x2 = objects.GameObject()
        x2.name = 'amulet'
        x2.appearance = "@"
        x2.color = "blue"

        (cx, cy) = (20, 9)
        GRID.nodes[(cx, cy)].objects.add(x1,x2)
        # player and lantern
        self.player = player.Player(GRID.nodes[(15,15)])
        self.player.weapon = objects.WEAPONS['axe1']
        objects.WEAPONS['axe1'].set_parent(self.player)
        self.player_sneakwalksprint = 1
        self.player_stand_state = 2
        self.player.lantern = objects.Lantern(10, self.player, lifetick=50)
        self.player.lantern.can_age = True
        self.player.flashlight = objects.Flashlight(14, 20, self.player)
        # self.player.flashlight.toggle()
        # self.player.flashlight = objects.Flashlight(6, 150, self.player) # realistic lantern.

        lantern_coord = (17,9)
        lantern = objects.Lantern(8, None)
        lantern.name = "lantern"
        lantern.appearance = 'A'
        lantern.color = "yellow"
        lantern.old_color = "yellow"
        self.lightsources = [self.player.lantern, self.player.flashlight, lantern]
        GRID.nodes[lantern_coord].objects.add(lantern)
        lantern.parent = GRID.nodes[lantern_coord]

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
                NEWS.add("You bump into the blocky white abyss.")
                # TODO: should be edge of AVAILABLE map
            elif GRID.nodes[(x,y)].is_passable():
                audio.play_movement(self.player_stand_state, self.player_sneakwalksprint, GRID.nodes[(x,y)].s_move)
                # self.player.set_position( (x,y) )
                self.player.set_parent(GRID.nodes[(x,y)])
                NEWS.add("")
            else:
                # it's an obstacle!  AKA gameobject
                if not self.is_visible((x,y)):
                    NEWS.add("You bump into something.") # TODO: material hints!
                    time.sleep(0.2)
                    # TODO:  CANNOT INTERACT IF CAN'T SEE ??????
                elif self.player.prefs.auto_attack and self.player.weapon:
                    obj = None
                    objs = GRID.nodes[(x,y)].objects

                    if len(objs) == 1:
                        obj = objs[0]
                    else:
                        damageable_objs = [obj for obj in objs if obj.damageable]
                        if len(damageable_objs) == 1:
                            obj = damageable_objs[0]

                    # only auto-attack damageable, impassible objects
                    if obj and obj.damageable and obj.impassible:
                        NEWS.add("You chop the {}!".format(obj.name))
                        self.player.weapon.attack(obj, self, GRID, layers.get("gameworld"))
                else:
                    NEWS.add("You bump into the {}.".format(GRID.nodes[(x,y)].name))

        elif key in list(map(ord, 'sS')):
            # toggle sneak/walk/sprint
            self.player_sneakwalksprint = (self.player_sneakwalksprint + 1) % 3
            NEWS.add("You begin {}.".format(SPEED_DICT[self.player_sneakwalksprint]))
            audio.play('weapons/trigger.aif', volume=0.2)
        elif key in list(map(ord, 'zZ')):
            # lower
            if self.player_stand_state > 0:
                self.player_stand_state -= 1
                if self.player_stand_state == 0:
                    NEWS.add("You go prone.")
                    audio.play('movement/changing/prone.aif')
                else:
                    NEWS.add("You crouch.")
                    audio.play('movement/changing/nonprone.aif')
        elif key in list(map(ord, 'xX')):
            # raise
            if self.player_stand_state < 2:
                self.player_stand_state += 1
                if self.player_stand_state == 1:
                    NEWS.add("You crouch.")
                else:
                    NEWS.add("You stand up.")
                audio.play('movement/changing/nonprone.aif')
        elif key == ord('l'):
            NEWS.add("You see: {}".format(', '.join(obj.name for obj in GRID.nodes[self.player.position()].objects if obj is not self.player)))

        if hasattr(self.player, 'flashlight'):
            _layer = layers.get("gameworld")

            if key == ord('f'):
                # toggle flashlight
                on = self.player.flashlight.toggle()
                NEWS.add("You switch your flashlight {}.".format("on" if on else "off"))
                time.sleep(0.2)

            elif key == ord('m'):
                mode = self.player.flashlight.toggle_mode()
                NEWS.add("You switch your flashlight to '{}' mode.".format(mode))

            elif key == ord('q'):
                self.player.flashlight.swivel(12, self, GRID, _layer)
            elif key == ord('Q'):
                self.player.flashlight.swivel(60, self, GRID, _layer)
            elif key == ord('e'):
                self.player.flashlight.swivel(-12, self, GRID, _layer)
            elif key == ord('E'):
                self.player.flashlight.swivel(-60, self, GRID, _layer)

            self.player.flashlight.update_direction(key_to_coord(key))

    def is_visible(self, absolute_coord):
        (x,y) = absolute_coord
        (px,py) = self.player.position()
        rx = x-px
        ry = y-py
        return (rx,ry) in self.visible

    def determine_occluders(self):
        return set(obj.position() for obj in objects.occluders())

    def determine_visible(self):

        ####################################
        # rendering
        occluded = self.determine_occluders()

        # all light sources individually
        visible = set().union(*(utils.visible_coords_absolute_2D(occluded, light, light.position()) for light in self.lightsources))

        ####################################
        # RELATIVE

        # add special overlaps (trees the player *can't* see but which block vision nonetheless)
        # faster now, since 'visible' is smaller
        visible = utils.remaining(
            relative_coords(visible,    self.player.position()),
            relative_coords(occluded,   self.player.position()),
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

    def interact(self, key):

        ####################################
        # TOP visual events pause interaction
        # since these are to be watched
        # BOTTOM visual events simply occur

        if not self.visual_events_top:
            self.handle_interaction(key)

    def age(self):
        # age player
        # age enemies
        layer = layers.get("gameworld")
        objects.GameObject.age_all(self, GRID, layer)
        objects.GameObject.kill_dead()

    def render_player(self):
        layer = layers.LayerManager.get("gameworld")

        p = self.player.position()
        # say('player is at {} {}'.format(*p))
        if (0,0) in self.visible:
            (fx,fy) = grid2d.xy_to_screen(p, p, *layer.size())
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
        NEWS_H = 5

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

        layers.get("news").resize(GAMEFRAME_W, NEWS_H)
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
        for event in self.visual_events_bottom:
            event.step()
        self.visual_events_bottom = [event for event in self.visual_events_bottom if not event.dead]

        # background
        self.determine_visible()
        grid2d.render_grid(self.visible, self.player.position(), layers.get("gameworld"), GRID.nodes)

        # player
        self.render_player()

        # exceptions
        for event in self.visual_events_top:
            event.step()
        self.visual_events_top = [event for event in self.visual_events_top if not event.dead]

        # foreground
        # TODO:
        # if not (self._truex, self._truey) == true_terminal_size():
        #     print '\a'

    def render_cycle(self):

        self.render_frame()
        self.render_GUI()
        render_to(layers.get("main"), self.stdscr)

    def render(self):
        """
        TICKS visual events!
        """

        self.render_cycle()
        while self.has_visual_events():

            time.sleep(self.visual_requested_wait())

            self.render_cycle()


    def render_GUI(self):
        if not self.window_too_small():
            layers.add_border(layers.get("main"), color=colors.fg_bg_to_index("white"))
            layers.get("main").setrange(0,0, "<main>", color=colors.fg_bg_to_index("white"))

            layers.get("gameworld").setrange(0, 0, "<gameworld>", color=colors.fg_bg_to_index("white"))

            layers.add_border(layers.get("gameframe"), color=colors.fg_bg_to_index("white"))
            layers.get("gameframe").setrange(0, 0, "<gameframe>", color=colors.fg_bg_to_index("white"))

            self.stats.render()
            layers.add_border(layers.get("stats"), color=colors.fg_bg_to_index("white"))
            layers.get("stats").setrange(0, 0, "<stats>", color=colors.fg_bg_to_index("white"))

            layers.add_border(layers.get("player"), color=colors.fg_bg_to_index("white"))
            layers.get("player").setrange(0, 0, "<player>", color=colors.fg_bg_to_index("white"))
            layers.get("player").setlines(5, 2, BODY, color=colors.fg_bg_to_index("white"))

            layers.add_border(layers.get("news"), color=colors.fg_bg_to_index("white"))
            layers.get("news").setrange(0, 0, "<news>", color=colors.fg_bg_to_index("white"))
            for (y, news) in enumerate(NEWS.latest(3), 1):
                layers.get("news").setrange(1, y, news, color=colors.fg_bg_to_index("white"))


    def playwrap(self):

        layers.set_curses_border()

        self.update_viewport(sound=False)
        self.render()

        try:
            while True:
                self.stats.inc()

                # input
                curses.flushinp()
                key = self.stdscr.getch()

                if key == -1: # TIMEOUT
                    pass # render!  update the nodes with multiple objects!

                elif key == curses.KEY_RESIZE:
                    self.update_viewport()
                    continue

                elif not self.window_too_small():
                    self.interact(key)
                    self.age()

                # render
                self.render()

        except KeyboardInterrupt:
            print("User quit.")

        print("Quit.")

    def play(self):
        try:
            self.playwrap()
        except Exception as e:
            import traceback
            # say(str(e), r=200)
            with open("BAD.txt", 'w') as f:
                f.write(traceback.format_exc())


def render_to(main_layer, stdscr):
    stdscr.erase()

    for (x, y, (char_or_code, color, _)) in list(main_layer.items()):
        try:
            if type(char_or_code) is int:
                stdscr.addch(y, x, char_or_code, color)
            else:
                stdscr.addstr(y, x, char_or_code if not PYTHON2 else char_or_code.encode(CODE), color)
        except curses.error:
            break

    stdscr.refresh()
