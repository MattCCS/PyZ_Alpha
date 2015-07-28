
import math

def convert_2D_coord_to_angle(coord):
    return math.degrees(math.atan2(*coord[::-1])) % 360

def coords_between_angles_2D(angle_table_2D, low, high):
    return set().union(*angle_table_2D[low:high+1])

def angles_around_angle_2D(angle, arc_width):
    return (angle - arc_width, angle + arc_width)

def coords_around_2D(angle_table_2D, angle, arc_width):
    return coords_between_angles_2D(angle_table_2D, *angles_around_angle_2D(angle, arc_width))

####################################

def angle_table(coords):
    return [set(c for c in coords if ang <= convert_2D_coord_to_angle(c) <= ang+1) for ang in xrange(360)]
