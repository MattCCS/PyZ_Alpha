
from pyz import audio
from pyz import utils
from pyz.vision import sightradius

####################################

CENTER = (0,0)

class Object(object):
    """
    An Object is any physically-interactive
    *thing* in the game world.
    """

    record = []
    
    def __init__(self, parent, position=CENTER):
        self.parent = parent
        self._position = position # relative to parent, if any
        Object.record.append(self)

    def position(self):
        if not self.parent:
            return self._position
        else:
            return utils.coords_add(self.parent.position(), self._position)

    def set_position(self, coord):
        self._position = coord

    def age(self):
        pass


class Item(Object):
    """
    An Item is a subset of Object -- it is a
    physically-interactive *thing* because we can
    place it/throw it/inspect it/etc., but it is
    also something that can be held/used/put in inventory.
    """

    record = []
    
    def __init__(self, parent, position=CENTER):
        Object.__init__(self, parent, position)
        Item.record.append(self)

    def age(self):
        pass

# TODO
# NOTE: don't call super if you care what is called/when/with what; call __init__ instead

class Lantern(Item, sightradius.SightRadius2D):

    def __init__(self, radius, parent, position=CENTER):
        Item.__init__(self, parent, position)
        sightradius.SightRadius2D.__init__(self, radius) # default shellcache/blocktable

        self.can_age = False
        self.lifetick = 10
        self.ticks = self.lifetick

    def visible_coords_absolute(self, blocked):
        return utils.visible_coords_absolute_2D(self.position, self, blocked)

    def age(self):
        if not self.can_age:
            return
        
        if not self.ticks:
            self.ticks = self.lifetick
            self.radius = max(0, self.radius - 1)
        else:
            self.ticks -= 1

class Flashlight(Item, sightradius.ArcLight2D):

    def __init__(self, radius, angle, arc_radius, parent, position=CENTER):
        Item.__init__(self, parent, position)
        sightradius.ArcLight2D.__init__(self, radius, angle, arc_radius) # default shellcache/blocktable/angletable

    def visible_coords_absolute(self, blocked):
        return utils.visible_coords_absolute_2D(self.position, self, blocked)


class Weapon(Item):

    def __init__(self, typ, beats, damage, damagetype):
        self.typ = typ

        self.beats = beats

        self.damage = damage
        self.damagetype = damagetype # damagetype vs beats??

    def attack_NODE(self, node):
        # damage conditional on material?
        if node.material in self.beats:
            try:
                audio.play_attack(self.typ, node.material)
                node.damage(self.damage)
            except Exception as e:
                import os
                # LOL:
                os.system("""osascript -e 'tell application "System Events" to display dialog "{}"'""".format(e))

WEAPONS = {}
WEAPONS['axe1'] = Weapon('axe', ['cloth', 'wood'], 1, 'slicing')
# piercing/blunt/slicing/crushing?

