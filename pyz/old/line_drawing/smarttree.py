"""
"""

import functools
import struct

import coord_gen_utils
import ray_tools

####################################

DIMENSIONS = 2

# \/ you can chagne this value!
MAX_RADIUS = 16 # SHOULD BE EVEN (ideally a power of 2)
RADIUS = (MAX_RADIUS - 1 - 1) / 2 # -1 for origin, -1 to keep even
# NOTE:  radius should be a positive int whose val == abs(min(coord int possible))

ORIGIN = (0,) * DIMENSIONS

####################################

def next_greater_power_of_2(x):
    """Includes x if x is a power of 2"""
    return 2**(x-1).bit_length()

def bytes_per_frame(number_of_coords, max_int=MAX_RADIUS, dimensions=DIMENSIONS):

    # always allocate at least one byte per coord
    # this isn't C, after all...
    bits_per_coord = max_int.bit_length()
    rounded_coord_int = next_greater_power_of_2(bits_per_coord)
    bytes_per_coord = 1 if rounded_coord_int < 8 else rounded_coord_int / 8
    total_coord_bytes = bytes_per_coord * dimensions

    # *frame* offset, not byte.
    # the number of frames == the number of coords
    bits_for_offset = number_of_coords.bit_length()
    rounded_offset_int = next_greater_power_of_2(bits_for_offset)
    total_offset_bytes = 1 if rounded_offset_int < 8 else rounded_offset_int / 8

    total = total_coord_bytes + total_offset_bytes

    return (total, (total_coord_bytes, (bytes_per_coord,) * dimensions, total_offset_bytes))

####################################

def generate_shells(radius, dimensions=2):
    """
    Generates all shells in [1,R-1]
    (does not include the origin)
    (does not include the radius)
    """
    return [coord_gen_utils.shell_wrap(i, dimensions=dimensions) for i in range(1, radius)]

####################################


def int_to_string(num, bytecount):
    """
    Does no checking -- you must be sure you don't chop off bytes

    Big-endian.

    Max: 4 bytes
    """
    return struct.pack('>L', num)[-bytecount:]

def form_data_frame(coord, coords_owned, bytes_per_coord, total_offset_bytes, adjust=RADIUS):
    bar = bytearray()
    for num in coord:
        bar += int_to_string(num + adjust, bytes_per_coord)
    bar += int_to_string(coords_owned, total_offset_bytes)
    return bar

def generate_uniques(shells, radius=RADIUS, dimensions=DIMENSIONS, echo=False):
    print("  radius:", RADIUS)

    endpoints = shells[-1]
    print("  endpoints:", endpoints)

    print("  Generating all rays...")
    all_rays = ray_tools.generate_all_rays(endpoints, dimensions)
    print("  all rays:", all_rays)

    print("Forming all_rays lookup table...")
    ray_lookup_table = ray_tools.form_ray_lookup_table(all_rays)

    print("  per shell:")
    uniques = {}

    number_of_coords = 0
    for (i, shell) in enumerate(shells):
        print("    Shell:", i)
        number_of_coords += len(shell)

        hit_sets = {}
        for coord in shell:
            all_hit = ray_tools.all_hit_by(coord, ray_lookup_table)
            hit_sets[coord] = all_hit
        if echo:
            print("    hit sets:", hit_sets)

        print("    UNIQUIFYING")
        for coord in shell:
            ours = hit_sets[coord]
            theirs = set(e for s in [val for (key, val) in [(k,v) for (k,v) in list(hit_sets.items()) if k != coord]] for e in s)
            unique = ours - theirs
            try:
                next_shell = shells[i+1]
            except IndexError:
                next_shell = set()
            unique_next = unique & next_shell
            if echo:
                print("      ours:", ours)
                print("      theirs:", theirs)
                print("      unique to {}: {}".format(coord, unique))
                print("      restricted to next shell: {}".format(unique_next))
                print()
            uniques[coord] = unique_next

    return (uniques, number_of_coords)

def generate_data_recursive(coords_to_render, uniques, frame_former):
    if not coords_to_render:
        return ''

    b = bytearray()
    for coord in coords_to_render:
        owned = uniques[coord]
        b += frame_former(coord, len(owned))
        b += generate_data_recursive(owned, uniques, frame_former)
    return b


# def generate_data_recursive(coords_to_render, uniques, frame_former):
#     if not coords_to_render:
#         return ''

#     b = bytearray()
#     while coords_to_render:
#         next_coords = []
#         for coord in coords_to_render:
#             owned = uniques[coord]
#             next_coords.append(owned)
#             b += frame_former(coord, len(owned))
#             b += generate_data_recursive(owned, uniques, frame_former)
#     return b

def combine_bytes(arr):
    return sum([val << (8 * i) for (i,val) in enumerate(reversed(arr))])

class ViewFastDataView(object):

    def __init__(self, data):
        self.data = bytearray(data) # I want ints.
        self.head = 0
        self.meta_offset = 4  # see formation function below

        self.bytes_per_coord = self.read()
        self.offset_bytes    = self.read()
        self.dimensions      = self.read()
        self.radius          = self.read()
        self.frame_size = (self.bytes_per_coord * self.dimensions) + self.offset_bytes

        self.size = len(self.data)

        print(vars(self))

        self.reset()

    def reset(self):
        self.head = self.meta_offset

    def step(self, i):
        self.head += i

    def read(self, i=1, inc=True):
        val = combine_bytes(self.data[self.head : self.head + i])
        if inc:
            self.step(i)
        return val

    def read_frame(self):
        """Reads one frame at the current head"""
        # print "head/size: {}/{}".format(self.head, self.size)
        if self.head == self.size:
            raise StopIteration

        # these walk forward
        coords = tuple((self.read(self.bytes_per_coord) - self.radius) for _ in range(self.dimensions))
        offset = self.read(self.offset_bytes)

        return (coords, offset)

    def skip_frames(self, n):
        self.step(self.frame_size * n)


class ViewFast(object):

    def __init__(self, data):
        self.dataview = ViewFastDataView(data)

    def visible_coords(self, blocked):
        visible = set()

        try:
            while True:
                (coords, offset) = self.dataview.read_frame()
                # print coords
                if coords in blocked:
                    self.dataview.skip_frames(offset)
                else:
                    visible.add(coords)
        except StopIteration:
            pass

        self.dataview.reset()

        return visible


def new(radius, dimensions):
    data = generate_data(radius, dimensions)

    return ViewFast(data)


def generate_data(radius=RADIUS, dimensions=DIMENSIONS):

    print("Generating shells...")
    shells = generate_shells(radius, dimensions)
    print("shells:", shells)

    print("Generating uniques...")
    (uniques, number_of_coords) = generate_uniques(shells, radius, dimensions)
    print("uniques:", uniques)

    for k in sorted(uniques, key=lambda k: len(uniques[k])):
        print(k, uniques[k])

    all_coords = set(uniques.keys())
    assert len(all_coords) == number_of_coords

    # add origin
    uniques[ORIGIN] = all_coords
    number_of_coords += 1
    print("UPDATED uniques:", uniques)

    (frame_bytes, (coord_bytes, coord_form, offset_bytes)) = bytes_per_frame(number_of_coords)

    print("NOC:", number_of_coords)
    print("FB:", frame_bytes)
    print("CB:", coord_bytes)
    print("CF:", coord_form)
    print("OB:", offset_bytes)

    bytes_per_coord = coord_form[0]

    former = functools.partial(form_data_frame,
                               bytes_per_coord=bytes_per_coord,
                               total_offset_bytes=offset_bytes,
                               adjust=radius)

    data = bytearray()
    data += int_to_string(bytes_per_coord, 1) # BYTES PER COORD BOUND TO 256 HERE
    data += int_to_string(offset_bytes, 1)    #    OFFSET BYTES BOUND TO 256 HERE
    data += int_to_string(dimensions, 1)      #      DIMENSIONS BOUND TO 256 HERE
    data += int_to_string(radius, 1)          #          RADIUS BOUND TO 256 HERE
    data += generate_data_recursive([ORIGIN], uniques, former) 

    print(list(map(int, data)))

    with open("TEST.txt", 'w') as f:
        f.write(data)

    return data

if __name__ == '__main__':
    # print generate_shells(3)
    # print generate_all_rays(coord_gen_utils.shell_wrap(2))
    print(bytes_per_frame(1))
    print(bytes_per_frame(13))
    print(bytes_per_frame(255))
    print(bytes_per_frame(256))
    print(generate_data())

