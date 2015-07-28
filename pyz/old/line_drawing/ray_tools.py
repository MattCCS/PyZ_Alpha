
import coord_gen_utils
import raytracing2

def generate_all_rays(shell, dimensions):
    return [list(raytracing2.gen_path_bounded_absolute( coord_gen_utils.origin(dimensions), coord )) for coord in shell]

def form_ray_lookup_table(all_rays):
    return [(ray, {coord:i for (i,coord) in enumerate(ray)}) for ray in all_rays]

def all_hit_by(start, ray_lookup_table):
    """Returns every coord even REMOTELY GRAZED by the given start coord"""
    hit = set()

    # all rays should be:
    # (ray, rayset)
    # --> ray = [coords]
    # --> rayset = {coord : i}
    #     ---> i = coord's index in 'ray'

    for (ray, rayset) in ray_lookup_table:
        if start in rayset:
            hit.update(ray[rayset[start]:])

    if start in hit:
        hit.remove(start)
    else:
        print "START NOT IN RAY...?", start

    return hit
