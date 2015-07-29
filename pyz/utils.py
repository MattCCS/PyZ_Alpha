
from pyz import log # <3

def coords_add(*coords):
    return tuple(map(sum, zip(*coords)))

def coord_invert(coord):
    return tuple(map(lambda n:-n, coord))

####################################

def remaining(potential, blocked, block_table):
    # crazy fast.
    return potential - set().union(*(block_table.get(coord, []) for coord in blocked))

def fast_hemiarc(arc_coords, cutoff, shellcache):

    if cutoff < float(shellcache.radius)/2:
        return arc_coords - shellcache.coords_before(cutoff+1)
    else:
        return arc_coords & shellcache.coords_after(cutoff+1)

@log.logwrap
def relevant_blocked(blocked_relative, radius, shellcache):
    return blocked_relative & shellcache.coords_before(radius)

@log.logwrap
def visible_coords_absolute_2D(blocked, view, position):
    (rx,ry) = position
    return {(vx+rx,vy+ry) for (vx,vy) in view.visible_coords({(x-rx, y-ry) for (x,y) in blocked})}

