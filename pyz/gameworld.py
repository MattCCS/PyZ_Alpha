# encoding: utf-8

import random

from pyz.curses_prep import CODE
from pyz.curses_prep import curses

from pyz import audio
from pyz import player
from pyz import objects
from pyz.vision.rays import arctracing
from pyz.vision import shell_tools
from pyz import utils

####################################
# SETTING UP THE LOGGER
import os
from pyz import log # <3
# ROOTPATH = os.path.splitext(__file__)[0]
# LOGPATH = "{0}.log".format(ROOTPATH)
# LOGGER = log.get(__name__, path=LOGPATH)
# LOGGER.info("----------BEGIN----------")

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
        self.has_player = False
        self.material = None
        self.appearance = None
        self.old_color = 0
        self.damageable = False
        self.health = 0
        self.set_dirt()

    def reset(self):
        self.unset_has_player()

    ####################################
    # permanent?

    def set_tree(self):
        self.name = 'tree'
        self.passable = False
        self.transparent = False
        self.damageable = True
        self.appearance = 'O'
        self.color = 5
        self.old_color = 5
        self.material = 'wood'
        self.health = random.randint(8,15)

    def set_smoke(self):
        self.name = 'smoke'
        self.passable = True
        self.transparent = False
        self.damageable = False
        self.appearance = random.choice("%&")
        # same material?
        self.material = 'dirt' # sound.
        self.color = 6
        self.old_color = 6

    def set_grass(self):
        self.name = 'grass'
        self.passable = True
        self.transparent = True
        self.damageable = False
        self.appearance = random.choice(",'\"`") # text
        self.material = 'grass'                  # sound
        self.color = random.choice([2,3])        # color
        self.old_color = self.color

    def set_dirt(self):
        self.name = 'dirt/clay'
        self.passable = True
        self.transparent = True
        self.material = 'dirt'
        self.appearance = '.'
        self.old_color = random.choice([7,7,7,7,7,5])
        self.color = self.old_color # default color
        self.damageable = False
        self.health = 0

    ####################################
    # temporary

    def set_has_player(self):
        self.has_player = True
        self.old_color = self.color
        self.color = 4

    def unset_has_player(self):
        self.has_player = False
        self.color = self.old_color

    ####################################

    def damage(self, n):
        if self.damageable:
            self.health -= n
            if self.health <= 0:
                self.die()

    def die(self):
        self.set_dirt()
        self.parentgrid.blocked.discard(self.coord)

    ####################################

    def code(self):
        return (self.passable, self.transparent)

    def code_num(self):
        return tup2bin(map(int, self.code()))

    def render(self, stdscr, x, y):

        if self.name == 'smoke':
            self.appearance = random.choice("%&")

        char = self.appearance if self.appearance else Node2D.ERROR

        if self.has_player:
            char = Node2D.PLAYER

        if not self.reverse_video:
            stdscr.addstr(y, x, char.encode(CODE), curses.color_pair(self.color))
        else:
            stdscr.addstr(y, x, char.encode(CODE), curses.A_REVERSE)

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

def say(s):
    import os
    os.system('say {}'.format(s))

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
        # self.player.lantern = objects.Lantern(16, self.player)
        # self.player.lantern.can_age = True
        self.player.flashlight = objects.Flashlight(24, 90, 15, self.player)

        lantern_coord = (17,9)
        self.lightsources = [self.player.flashlight, objects.Lantern(8, None, lantern_coord)]
        self.nodes[lantern_coord].set_dirt()
        self.nodes[lantern_coord].appearance = 'X'
        self.nodes[lantern_coord].color = 4
        self.nodes[lantern_coord].old_color = 4

    def reset(self, coords=None):
        if coords is None:
            nodes = self.nodes.itervalues()
        else:
            nodes = (self.nodes[coord] for coord in coords)

        for node in nodes:
            node.reset()

    def frame_coords_2D(self):
        (px, py) = self.player.position()

        # # ABSOLUTE, around player
        # for y in xrange(py+self.y/2-1, py-self.y/2-1, -1):
        #     yield [(x,y) for x in xrange(px-self.x/2, px+self.x/2)]

        # for y in xrange(py + RADIUS - 1, py - RADIUS - 1, -1):
        #     yield [(x,y) for x in xrange(px-RADIUS, px+RADIUS)]

        for y in xrange(py + self.y/2 - 1, py - self.y/2 - 1, -1):
            yield [(x,y) for x in xrange(px-self.x, px+self.x)]


    def render(self, visible, stdscr):

        SPACING = 2
        BORDER_OFFSET_X = 1
        BORDER_OFFSET_Y = 1

        (px,py) = self.player.position()

        for row in self.frame_coords_2D():

            try:
                for (x,y) in row:

                    if not (x, y) in self.nodes:
                        try:
                            stdscr.addstr(self.viewy/2-y-1-BORDER_OFFSET_Y+py, x*SPACING+BORDER_OFFSET_X-px*SPACING+self.viewx/2, u'█'.encode(CODE))
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
                            # self.nodes[(x,y)].render(stdscr, x*SPACING+BORDER_OFFSET_X+self.x-px*2, final_y+BORDER_OFFSET_Y+self.y/2+py-self.viewy)
                            self.nodes[(x,y)].render(stdscr, x*SPACING+BORDER_OFFSET_X-px*SPACING+self.viewx/2, self.viewy/2-y-1-BORDER_OFFSET_Y+py)
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

            elif key == ord('m'):
                self.player.flashlight.toggle_mode(self, stdscr, None)

            diff = utils.coord_diff((oldx,oldy), self.player.position())
            self.player.flashlight.update_direction(diff)

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

    # @profile
    # @log.logwrap
    def tick(self, key, stdscr):
        import time

        for obj in objects.Object.record:
            obj.age(self, stdscr)

        # TODO: \/
        stdscr.erase() # should erase() be INSIDE phase 2?  need a better understanding.
        self.tick_phase_1(key, stdscr)
        self.tick_phase_2(stdscr)
        while self.has_visual_events():
            time.sleep(0.05) # <--- need to standardize this wait time!
            stdscr.clear()
            self.tick_phase_2(stdscr) # this must decrement visual events
            stdscr.refresh()
            # TODO: ^
        stdscr.refresh()
        self.tick_phase_3(stdscr)

    def tick_phase_1(self, key, stdscr):

        ####################################
        # visual events pause interaction

        if key == curses.KEY_RESIZE:
            self.update_viewport(stdscr)
            curses.resize_term(self.viewy, self.viewx)
            stdscr.refresh()
            audio.play("weapons/trigger.aif", volume=0.2)

        elif not self.has_visual_events():
            self.handle_interaction(key, stdscr)

        # player
        self.nodes[self.player.position()].set_has_player()

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

        # exceptions
        for event in self.visual_events_top:
            event.step()
        self.visual_events_top = [event for event in self.visual_events_top if not event.dead]

        # foreground
        stdscr.border()
        stdscr.addstr(0, 0, "player: {}".format(self.player.position()))
        stdscr.addstr(1, 0, "standing status: {}".format(STANDING_DICT[self.player_stand_state]))
        stdscr.addstr(2, 0, "speed status: {}".format(SPEED_DICT[self.player_sneakwalksprint]))
        stdscr.addstr(3, 0, "screen dimensions: {}".format( (self.viewx, self.viewy) ))

    def tick_phase_3(self, stdscr):

        self.reset() # <--- improve this


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

                # tick
                self.tick(key, stdscr)
        except KeyboardInterrupt:
            print "User quit."

        print "Quit."
