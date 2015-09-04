
from pyz import audio
from pyz import utils
from pyz.vision import sightradius
from pyz.vision import arc_tools
from pyz import events
from pyz import log

####################################

CENTER = (0,0)

class NoSpaceException(Exception): pass

class GameObject(object):
    """
    A GameObject is any physically-interactive
    *thing* in the game world (that takes up one space).
    """

    record = []
    
    def __init__(self, parent, position=CENTER):
        self.parent = parent
        self._position = position # relative to parent, if any
        GameObject.record.append(self)

    def position(self):
        if not self.parent:
            return self._position
        else:
            return utils.coords_add(self.parent.position(), self._position)

    def set_position(self, coord):
        self._position = coord

    def age(self, grid, stdscr):
        pass


class Item(GameObject):
    """
    An Item is a subset of GameObject -- it is a
    physically-interactive *thing* because we can
    place it/throw it/inspect it/etc., but it is
    also something that can be held/used/put in inventory.
    """

    record = []
    
    def __init__(self, parent, position=CENTER):
        GameObject.__init__(self, parent, position)
        Item.record.append(self)

    def age(self, grid, stdscr):
        pass

# TODO
# NOTE: don't call super if you care what is called/when/with what; call __init__ instead

class Lantern(Item, sightradius.SightRadius2D):
    """
    Represets a radial light source.
    """

    def __init__(self, radius, parent, position=CENTER):
        Item.__init__(self, parent, position)
        sightradius.SightRadius2D.__init__(self, radius) # default shellcache/blocktable

        self.can_age = False
        self.lifetick = 10
        self.ticks = self.lifetick

    def age(self, grid, stdscr):
        if not self.can_age:
            return

        if not self.ticks:
            self.ticks = self.lifetick
            self.radius = max(0, self.radius - 1)
        else:
            self.ticks -= 1


class Flashlight(Item, sightradius.ArcLight2D):
    """
    Represets a directed radial light source.
    """

    def __init__(self, radius, angle, arc_length, parent, position=CENTER):
        Item.__init__(self, parent, position)
        sightradius.ArcLight2D.__init__(self, radius, angle, arc_length) # default shellcache/blocktable/angletable

        self.on = True
        self.focus = (20,30)
        self.modes = ['static', 'facing', 'focus']
        self.mode = 0
        self.focus_threshold = self.arc_length / 2
        self.focus_speed = 12

    def visible_coords(self, blocked_relative):
        if not self.on:
            return set()
        else:
            return sightradius.ArcLight2D.visible_coords(self, blocked_relative)

    def toggle(self):
        audio.play("items/flashlight_toggle.m4a", volume=3.0)
        self.on = not self.on

    def toggle_mode(self):
        audio.play("weapons/trigger.aif", volume=0.2)
        self.mode = (self.mode + 1) % len(self.modes)

    def is_focusing(self):
        return self.modes[self.mode] == 'focus'

    def target_angle_diff(self):
        return int(round(arc_tools.relative_angle(self.position(), self.focus)))

    def facing_away(self):
        return abs(self.target_angle_diff() - self.angle) > self.focus_threshold

    def update(self, grid, stdscr):
        target = self.target_angle_diff()
        grid.visual_events_bottom.append(events.FacingEvent(grid, stdscr, None, self, self.angle, target, self.focus_speed))
        grid.visual_events_top.append(events.GenericFocusEvent(grid, stdscr, self.focus))
    
    @log.logwrap
    def update_direction(self, direction):
        if self.modes[self.mode] != 'facing':
            return

        if direction == (1,0):
            self.angle = 0
        elif direction == (0,1):
            self.angle = 90
        elif direction == (-1,0):
            self.angle = 180
        elif direction == (0,-1):
            self.angle = 270

    def age(self, grid, stdscr):
        if self.on and self.facing_away() and self.is_focusing():
            self.update(grid, stdscr)


class Container(Item):

    def __init__(self, capacity, parent, position):
        Item.__init__(self, parent, position)
        self.items = set()
        self.capacity = capacity
        self.remaining = self.capacity

    def store(self, item):
        if self.remaining - item.size() < 0:
            return False
        else:
            self.remaining -= item.size()
            self.items.add(item)
            return True

    def remove(self, item):
        if item in self.items:
            self.items.remove(item)
            self.remaining += item.size()
            return True
        else:
            return False # not found


class Weapon(Item):

    def __init__(self, typ, beats, damage, damagetype):
        self.typ = typ

        self.beats = beats

        self.damage = damage
        self.damagetype = damagetype # damagetype vs beats??

    @log.logwrap
    def attack_NODE(self, node, grid, stdscr, coord):
        # damage conditional on material?
        if node.material in self.beats:
            audio.play_attack(self.typ, node.material)
            node.damage(self.damage)
            # grid.visual_events_top.append(events.GenericInteractVisualEvent(grid, stdscr, coord))

WEAPONS = {}
WEAPONS['axe1'] = Weapon('axe', ['cloth', 'wood'], 1, 'slicing')
# piercing/blunt/slicing/crushing?

