
from pyz import objects

class Player(objects.GameObject):

    def __init__(self, parent=None, position=(20,20)):
        objects.GameObject.__init__(self, parent, position)

        self.weapon = None

        self.prefs = Preferences()

        # dayZ
        self.temperature = 50 # /100?
        self.thirst = 50 # /100?
        self.blood = 10000
        self.hunger = 50 # /100?

        self.stress = 0 # fear?

        self.wetness = 0 # ?

        self.stats = Stats()
        
        # self.inventory = [] # <--- does this not make sense?  considering body parts can have attachments

        self.body = Body()


class Preferences(object):

    def __init__(self):

        self.auto_attack = True


class Stats(object):
    
    def __init__(self):

        self.agility    = 10
        self.strength   = 10
        self.dodge      = 10
        self.stealth    = 10
        self.defense    = 10
        self.perception = 10



class Body(object):

    def __init__(self):
        pass


class BodyPart(object):
    
    def __init__(self):
        self.weight = 0
        self.attachments = []
        self.attachments_allowed = set()
