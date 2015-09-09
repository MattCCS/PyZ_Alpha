
from pyz import audio
from pyz.vision import utils
from pyz.vision import sightradius
from pyz.vision import arc_tools
from pyz import events
from pyz import log
from pyz import data

####################################

def say(s, r=400):
    import subprocess
    subprocess.check_output(['say', s, '-r', str(r)])

CENTER = (0,0)

####################################

DAMAGE_DESCRIPTORS = [
    (0.1, "near-broken"),
    (0.2, "extremely damaged"),
    (0.3, "heavily damaged"),
    (0.4, "damaged"),
    (0.5, "gouged"),
    (0.6, "scraped"),
    (0.7, "dented"),
    (0.8, "scratched"),
    (0.9, "worn"),
    (1.0, ""),
]

def damage_descriptor(p):
    assert 0 <= p <= 1.0

    for (c, d) in DAMAGE_DESCRIPTORS:
        if p < c:
            val = d
            break
    else:
        val = ""

    return " " + val

####################################

def make(name, parent):
    gob = GameObject(parent=parent)
    data.reset(gob, "object", name)
    return gob

def occluders():
    return GameObject.occluders()

####################################

class GameObject(object):
    """
    A GameObject is any physically-interactive
    *thing* in the game world (that takes up one space).
    """

    record = []

    @staticmethod
    def age_all(grid, layer):
        for obj in GameObject.record:
            obj.age(grid, layer)

    @staticmethod
    def kill_dead():
        dead = [obj for obj in GameObject.record if obj.dead]
        for obj in dead:
            GameObject.record.remove(obj)  # remove from record
            obj.parent.objects.remove(obj) # remove from parent
            # del obj

    @staticmethod
    def occluders():
        """Dynamic!"""
        return (obj for obj in GameObject.record if obj.occluder)
    
    ####################################

    def __init__(self, parent=None, position=CENTER):
        self.dead = False
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

    def age(self, grid, layer):
        pass

    def damage(self, n):
        if self.damageable:
            self.health -= n
            if self.health <= 0:
                # self.parentgrid.news.add("The {} dies.".format(self.name))
                self.dead = True
                if hasattr(self, "s_death"):
                    (sound, volume) = self.s_death
                    audio.play_random(sound, volume)

    ####################################

    def __getattr__(self, key):
        """Sexy."""

        # DO error if asked for missing field:
        if not key in vars(self) and key in data.ATTRIBUTES:
            return False
        else:
            return vars(self)[key]


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

    def age(self, grid, layer):
        pass

# TODO
# NOTE: don't call super if you care what is called/when/with what; call __init__ instead

class Lantern(Item, sightradius.SightRadius2D):
    """
    Represets a radial light source.
    """

    def __init__(self, radius, parent, lifetick=20, position=CENTER):
        Item.__init__(self, parent, position)
        sightradius.SightRadius2D.__init__(self, radius) # default shellcache/blocktable

        self.can_age = False
        self.lifetick = lifetick
        self.ticks = self.lifetick

    def age(self, grid, layer):
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

    def __init__(self, radius, arc_length, parent, angle=0, position=CENTER):
        Item.__init__(self, parent, position)
        sightradius.ArcLight2D.__init__(self, radius, angle, arc_length) # default shellcache/blocktable/angletable

        self.on = True
        self.focus = (20, 30)
        self.modes = ['static', 'facing', 'focus']
        self.mode = 1
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
        return self.on

    def swivel(self, diff, grid, layer):
        self.mode = 0 # OVERRIDE
        target = (self.angle + diff) % 360
        grid.visual_events_bottom.append(events.FacingEvent(grid, layer, None, self, self.angle, target, self.focus_speed))

    def toggle_mode(self):
        audio.play("weapons/trigger.aif", volume=0.2)
        self.mode = (self.mode + 1) % len(self.modes)
        return self.modes[self.mode]

    def is_focusing(self):
        return self.modes[self.mode] == 'focus'

    def target_angle_diff(self):
        return int(round(arc_tools.relative_angle(self.position(), self.focus)))

    def facing_away(self):
        return abs(self.target_angle_diff() - self.angle) > self.focus_threshold

    def update(self, grid, layer):
        target = self.target_angle_diff()
        grid.visual_events_bottom.append(events.FacingEvent(grid, layer, None, self, self.angle, target, self.focus_speed))
        grid.visual_events_top.append(events.GenericFocusEvent(grid, layer, self.focus))

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

    def age(self, grid, layer):
        if self.on and self.is_focusing() and self.facing_away():
            self.update(grid, layer)


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
    def attack(self, obj, grid, layer):
        # damage conditional on material?
        audio.play_attack(self.typ, obj.material)
        grid.visual_events_top.append(events.GenericInteractVisualEvent(grid, layer, obj.position()))
        if obj.material in self.beats:
            obj.damage(self.damage)

WEAPONS = {}
WEAPONS['axe1'] = Weapon('axe', ['cloth', 'wood'], 1, 'slicing')
# piercing/blunt/slicing/crushing?

