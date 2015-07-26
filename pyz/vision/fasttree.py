
import coord_gen_utils
import ray_tools

import ast

####################################

FILENAME_FORM = "RAYS_{dimensions}D_{radius}.txt"

def filename_format(radius, dimensions):
    return FILENAME_FORM.format(radius=radius, dimensions=dimensions)

####################################

class SimpleView(object):

    def __init__(self, table, radius, dimensions):
        self.radius = radius
        self.dimensions = dimensions
        self.table = table  # coord -> everything it blocks (even partially)
        self.all = set(table.keys())

    def visible_coords(self, blocked):
        # crazy fast.
        return self.all - set().union(*(self.table.get(coord, []) for coord in blocked))

    def save(self):
        return str(self.table)

    def filename(self):
        return filename_format(self.radius, self.dimensions)

####################################

def save(view):
    with open(view.filename(), 'w') as f:
        f.write(view.save())

def load(radius, dimensions):
    with open(filename_format(radius, dimensions), 'r') as f:
        return SimpleView(ast.literal_eval(f.read()), radius, dimensions)

####################################

def gen_new(radius, dimensions):

    # TODO:
    # DOES NOT INCLUDE (0,0) !!!
    # is that ok?
    print "Generating radius:{} dimensions:{}".format(radius, dimensions)

    print "Generating all points..."
    all_points = coord_gen_utils.shell_coords(0, radius, dimensions)

    print "Generating endpoints..."
    endpoints = coord_gen_utils.shell_wrap(radius, dimensions)
    # print "endpoints:", endpoints

    print "Calculating all rays..."
    all_rays = ray_tools.generate_all_rays(endpoints, dimensions)
    # print "all rays:", all_rays

    print "Forming all_rays lookup table..."
    ray_lookup_table = ray_tools.form_ray_lookup_table(all_rays)

    print "Finding all hit by..."
    table = {}
    for coord in all_points:
        all_hit = ray_tools.all_hit_by(coord, ray_lookup_table)
        table[coord] = all_hit

    print "done."
    return SimpleView(table, radius, dimensions)

####################################

def gen_new_all(radii=[8,12,16,24,32,48,64], dimensions=[2]):
    for dim in dimensions:
        for rad in radii:
            print "Generating/saving radius:{} dimensions:{}".format(rad, dim)
            save(gen_new(rad, dim))

####################################

if __name__ == '__main__':
    # sv = gen_new(8,2)
    # print sv
    # print sv.save()

    gen_new_all()
    # gen_new_all(radii=[8,12,16,24,32], dimensions=[3])

