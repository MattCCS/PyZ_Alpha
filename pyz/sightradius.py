
from pyz.vision import coord_gen_utils
from pyz.vision import fasttree


class SightRadius(object):

    def __init__(self, radius, dimensions):
        self.radius = radius
        self.dimensions = dimensions
        (self.view, self.angle_table) = fasttree.gen_new(radius, dimensions)

    def visible_coords(self, blocked):
        return self.view.visible_coords(blocked)


class ArcLight(SightRadius):

    def __init__(self, radius, dimensions, angle, arc_width):
        super(ArcLight, self).__init__(radius, dimensions)
        self.angle = angle
        self.arc_width = arc_width

    def visible_coords(self, blocked):
        return self.view.visible_coords(blocked) & coord_gen_utils.coords_around_2D(self.angle_table, self.angle, self.arc_width)

    def set_angle(self, angle):
        self.angle = angle

    def set_arc(self, arc):
        self.arc_width = arc

