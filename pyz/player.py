
class Player(object):

    def __init__(self):

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



class Stats(object):
    
    def __init__(self):

        self.agility = 10
        self.strength = 10
        self.dodge = 10
        self.stealth = 10
        self.defense = 10



class Body(object):

    def __init__(self):
        pass


class BodyPart(object):
    
    def __init__(self):
        self.weight = 0
        self.attachments = []
        self.attachments_allowed = set()
