# encoding: utf-8

import random
import time

from pyz.curses_prep import CODE
from pyz.curses_prep import curses

from pyz import audio
from pyz import player
from pyz import objects
from pyz import data
from pyz.vision.rays import arctracing
from pyz.vision import shell_tools
from pyz import utils

####################################
# SETTING UP THE LOGGER
import os
from pyz import log # <3
ROOTPATH = os.path.splitext(__file__)[0]
LOGPATH = "{0}.log".format(ROOTPATH)
LOGGER = log.get(__name__, path=LOGPATH)
LOGGER.info("----------BEGIN----------")

####################################

def relative_coords(coords, rel_coord):
    (rx, ry) = rel_coord
    return set([(x-rx, y-ry) for (x,y) in coords])

def tup2bin(tup):
    return int(''.join(map(str, tup)), 2)

def bin2tup(n):
    return tuple(map(int, bin(n)[2:]))

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

def say(s):
    import subprocess
    # subprocess.check_output(['say', s, '-r', '400'])

####################################

class Node2D(object):

    HIDDEN = u'█'
    PLAYER = 'P'
    SOLID  = 'O'
    GLASS  = '/'
    SMOKE  = '%'
    AIR    = '.'
    ERROR  = '!'

    def __init__(self, parentgrid, code, coord):
        # passable, transparent
        # 1 1 = air
        # 1 0 = fog/smoke
        # 0 1 = glass
        # 0 0 = solid

        if type(code) is int:
            code = bin2tup(code)

        self.parentgrid = parentgrid
        self.coord = coord

        self.reverse_video = False

        self.name = '---'
        self.passable, self.transparent = code
        # self.has_player = False
        self.material = None
        self.appearance = None
        self.color = 0
        self.old_color = 0
        self.damageable = False
        self.health = 0
        self.objects = []
        self.set_dirt()

    # def reset(self):
    #     self.unset_has_player()

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

    ####################################

    def code(self):
        return (self.passable, self.transparent)

    def code_num(self):
        return tup2bin(map(int, self.code()))

    def render(self, stdscr, x, y):
        if self.name == 'tree':
            LOGGER.debug('tree color -- {}'.format(self.color))

        if self.name == 'smoke':
            self.appearance = random.choice("%&")

        char = self.appearance if self.appearance else Node2D.ERROR

        # if self.has_player:
        #     char = Node2D.PLAYER

        try:
            if not self.reverse_video:
                stdscr.addstr(y, x, char.encode(CODE), curses.color_pair(self.color))
            else:
                stdscr.addstr(y, x, char.encode(CODE), curses.A_REVERSE)
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

    for n in xrange(first):
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

    def __init__(self, x, y, player_view, blocked_set):
        
        self.x = x
        self.y = y
        self.viewx = x
        self.viewy = y

        self.nodes = {coord : Node2D(self, 3, coord) for coord in yield_coords( (self.x, self.y) )}

        self.blocked = blocked_set
        for coord in blocked_set:
            self.nodes[coord].set_tree()

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

        # self.nodes[(cx,cy)].set_tree()
        # self.blocked.add((cx,cy))

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
        self.lightsources = [self.player.lantern, objects.Lantern(8, None, lantern_coord)]
        self.nodes[lantern_coord].set_dirt()
        self.nodes[lantern_coord].appearance = 'X'
        self.nodes[lantern_coord].color = 4
        self.nodes[lantern_coord].old_color = 4

    # def reset(self, coords=None):
    #     if coords is None:
    #         nodes = self.nodes.itervalues()
    #     else:
    #         nodes = (self.nodes[coord] for coord in coords)

    #     for node in nodes:
    #         node.reset()

    def frame_coords_2D(self):
        (px, py) = self.player.position()

        # # ABSOLUTE, around player
        # for y in xrange(py+self.y/2-1, py-self.y/2-1, -1):
        #     yield [(x,y) for x in xrange(px-self.x/2, px+self.x/2)]

        # for y in xrange(py + RADIUS - 1, py - RADIUS - 1, -1):
        #     yield [(x,y) for x in xrange(px-RADIUS, px+RADIUS)]

        for y in xrange(py + self.y/2 - 1, py - self.y/2 - 1, -1):
            yield [(x,y) for x in xrange(px-self.x, px+self.x)]

    def x_to_screen(self, x, px, BORDER_OFFSET_X=1, spacing=2):
        return x*spacing - px*spacing + BORDER_OFFSET_X + self.viewx/2

    def y_to_screen(self, y, py, BORDER_OFFSET_Y=1):
        return self.viewy/2 - y + py - BORDER_OFFSET_Y - 1

    def xy_to_screen(self, coord, ppos, spacing=2, BORDER_OFFSET_X=1, BORDER_OFFSET_Y=1):
        (x,y) = coord
        (px,py) = ppos
        fx = self.x_to_screen(x, px, BORDER_OFFSET_X=BORDER_OFFSET_X, spacing=2)
        fy = self.y_to_screen(y, py, BORDER_OFFSET_Y=BORDER_OFFSET_Y)
        return (fx, fy)

    def render(self, visible, stdscr):

        (px,py) = self.player.position()

        for row in self.frame_coords_2D():

            try:
                for (x,y) in row:

                    fx = self.x_to_screen(x, px)
                    fy = self.y_to_screen(y, py)

                    if not (x, y) in self.nodes:
                        try:
                            stdscr.addstr(fy, fx, u'█'.encode(CODE))
                        except curses.error:
                            pass
                        # pass
                    elif not (x-px, y-py) in visible:
                        # X/Y are REAL coords (non-relative)
                        # so to check for visibility, we have to relativize them
                        pass
                    else:
                        try:
                            stdscr.addstr(9, 0, " "*30)
                            stdscr.addstr(10, 0, " "*30)
                            stdscr.addstr(9, 0, "x, self.x, px, px*2: {}/{}/{}/{}".format(x, self.x, px, px*2))
                            stdscr.addstr(10, 0, "y, self.y, self.viewy: {}/{}/{}".format(y, self.y, self.viewy))
                            self.nodes[(x,y)].render(stdscr, fx, fy)
                            # self.nodes[(x+self.x/2,y+self.y/2)].render(stdscr, x*2, y)
                        except KeyError:
                            pass # node out of bounds

                    # stdscr.addstr(final_y, x*2+1, ' ')

            except curses.error:
                pass # screen is being resized, probably.


    def update_viewport(self, stdscr):
        self.viewy, self.viewx = stdscr.getmaxyx()

    @log.logwrap
    def handle_interaction(self, key, stdscr):

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
                    self.player.weapon.attack_NODE(self.nodes[(x,y)], self, stdscr, (x,y))

        elif key in map(ord, 'sS'):
            # toggle sneak/walk/sprint
            self.player_sneakwalksprint = (self.player_sneakwalksprint + 1) % 3
            audio.play('weapons/trigger.aif', volume=0.2)
        elif key in map(ord, 'zZ'):
            # lower
            if self.player_stand_state > 0:
                self.player_stand_state -= 1
                if self.player_stand_state == 0:
                    audio.play('movement/changing/prone.aif')
                else:
                    audio.play('movement/changing/nonprone.aif')
        elif key in map(ord, 'xX'):
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
                self.player.flashlight.toggle_mode(self, stdscr)

            self.player.flashlight.update_direction(key_to_coord(key))

        stdscr.addstr(7, 0, "old player: {}".format( (oldx, oldy) ))

    def determine_visible(self):

        ####################################
        # rendering
        ####################################
        # ASBOLUTE
        visible = set()

        # add all light sources
        for light in self.lightsources:
            _blocked_relative = relative_coords(self.blocked, light.position())
            _blocked_relative = utils.relevant_blocked(_blocked_relative, light.radius, shell_tools.CACHE) # saves work
            # _visible = utils.visible_coords_absolute_2D(_blocked, light, light.position())
            _visible = light.visible_coords(_blocked_relative)
            _visible = relative_coords(_visible, utils.coord_invert(light.position()))
            visible.update(_visible)

        ####################################
        # RELATIVE
        visible = relative_coords(visible, self.player.position()) # now relative to player!!

        # add special overlaps (trees the player *can't* see but which block vision nonetheless)
        # faster now, since 'visible' is smaller
        _player_blocked_relative = relative_coords(self.blocked, self.player.position())
        _player_potential_relative = utils.remaining(visible, _player_blocked_relative, arctracing.BLOCKTABLE)

        visible &= _player_potential_relative

        # if we're in smoke, show adjacents
        if visible == set( [(0,0)] ):
            visible.update( [(1,0), (-1,0), (0,-1), (0,1)] )

        return visible

    def has_visual_events(self):
        return bool(self.visual_events_top) or bool(self.visual_events_bottom)

    def visual_requested_wait(self):
        if self.requested_waits:
            wait = max(self.requested_waits)
            self.requested_waits = []
        else:
            wait = 0

        return wait

    # @profile
    @log.logwrap
    def tick(self, key, stdscr):
        import time

        # TODO: \/
        stdscr.erase() # should erase() be INSIDE phase 2?  need a better understanding.
        self.tick_phase_1(key, stdscr)

        for obj in objects.GameObject.record:
            obj.age(self, stdscr)

        self.tick_phase_2(stdscr)

        stdscr.refresh()

        if self.has_visual_events():
            while self.has_visual_events():

                time.sleep(self.visual_requested_wait()) # <--- need to standardize this wait time!  or dynamicize it??

                stdscr.erase()

                self.tick_phase_2(stdscr) # this *must* decrement all visual events.

                stdscr.refresh()

        self.tick_phase_3()

    def tick_phase_1(self, key, stdscr):

        ####################################
        # TOP visual events pause interaction
        # since these are to be watched
        # BOTTOM visual events simply occur

        if key == curses.KEY_RESIZE:
            self.update_viewport(stdscr)
            curses.resize_term(self.viewy, self.viewx)
            stdscr.refresh()
            audio.play("weapons/trigger.aif", volume=0.2)

        elif not self.visual_events_top:
            self.handle_interaction(key, stdscr)

        # player
        # self.nodes[self.player.position()].set_has_player()

    def tick_phase_2(self, stdscr):
        # RENDERING
        
        ####################################
        # META-RENDERING

        # modifiers
        for event in self.visual_events_bottom:
            event.step()
        self.visual_events_bottom = [event for event in self.visual_events_bottom if not event.dead]

        # background
        self.render(self.determine_visible(), stdscr)

        # player
        self.render_player(stdscr)

        # exceptions
        for event in self.visual_events_top:
            event.step()
            # os.system('say ok')
        self.visual_events_top = [event for event in self.visual_events_top if not event.dead]

        # foreground
        stdscr.border()
        stdscr.addstr(0, 0, "player: {}".format(self.player.position()))
        stdscr.addstr(1, 0, "standing status: {}".format(STANDING_DICT[self.player_stand_state]))
        stdscr.addstr(2, 0, "speed status: {}".format(SPEED_DICT[self.player_sneakwalksprint]))
        stdscr.addstr(3, 0, "screen dimensions: {}".format( (self.viewx, self.viewy) ))

    def tick_phase_3(self):

        # self.reset() # <--- improve this
        pass

    def render_player(self, stdscr):
        p = self.player.position()
        (fx,fy) = self.xy_to_screen(p, p)
        stdscr.addstr(fy, fx, Node2D.PLAYER, curses.color_pair(4)) # TODO: NOT 4 !!!

    def resize(self, stdscr):
        stdscr.erase()

        self.update_viewport(stdscr)
        curses.resize_term(self.viewy, self.viewx)
        stdscr.refresh()
        audio.play("weapons/trigger.aif", volume=0.2)

        self.render(self.determine_visible(), stdscr)
        self.render_player(stdscr)

        stdscr.refresh()

    def play(self, stdscr):

        print "Playing..."

        self.update_viewport(stdscr)
        stdscr.clear()
        self.tick('', stdscr)  # start

        try:
            while True:
                # input
                curses.flushinp()
                key = stdscr.getch()

                if key == 113: # q
                    break

                if key == curses.KEY_RESIZE:
                    self.resize(stdscr)
                    continue

                # tick
                self.tick(key, stdscr)
        except KeyboardInterrupt:
            print "User quit."

        print "Quit."
