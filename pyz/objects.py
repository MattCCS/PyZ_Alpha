
from pyz import audio

class Object(object):
    """
    An Object is any physically-interactive
    *thing* in the game world.
    """
    pass


class Item(Object):
    """
    An Item is a subset of Object -- it is a
    physically-interactive *thing* because we can
    place it/throw it/inspect it/etc., but it is
    also something that can be equipped/used/put in inventory.
    """
    pass

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

