
# Adapted from http://www.redblobgames.com/pathfinding/

import abc
import time
import heapq

class PriorityQueue(object):
    def __init__(self):
        self.elements = []
    
    def empty(self):
        return len(self.elements) == 0
    
    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))
    
    def get(self):
        return heapq.heappop(self.elements)[1]

####################################

def heuristic(a, b):
    (x1, y1) = a
    (x2, y2) = b
    return abs(x1 - x2) + abs(y1 - y2)

####################################

def extract_path(came_from, goal):

    steps = []
    current = goal

    while True:
        steps.append(current)
        current = came_from[current]
        if current is None:
            break

    return reversed(steps)

def my_a_star(graph, start, goal):
    frontier = PriorityQueue()
    frontier.put(start, 0)
    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0

    while not frontier.empty():
        current = frontier.get()
        
        if current == goal:
            return extract_path(came_from, goal)
        
        for next_ in graph.neighbors(current):
            new_cost = cost_so_far[current] + graph.cost(current, next_)
            if next_ not in cost_so_far or new_cost < cost_so_far[next_]:
                cost_so_far[next_] = new_cost
                priority = new_cost + heuristic(goal, next_)
                frontier.put(next_, priority)
                came_from[next_] = current

####################################

def cardinal_neighbors(coord):
    points = set()
    for i in xrange(len(coord)):
        val = coord[i]
        pre = coord[:i]
        post = coord[i+1:]
        points.add(pre + (val-1,) + post)
        points.add(pre + (val+1,) + post)
    return points

def flood_fill(graph, start):
    """
    Flood-fills the graph from start.
    Graph must be a mapping of {hashable -> set(hashable)}
    """

    seen = set()
    frontier = set([start])

    while frontier:
        seen.update(frontier)
        frontier = set().union(*(graph[n] for n in list(frontier) if n in graph)) - seen

    return seen

####################################

class Mesh(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, dimensions, corner):
        assert len(dimensions) == len(corner)

        self.mins = tuple(corner)
        self.maxs = tuple(a+b for a,b in zip(dimensions, corner))

    def contains(self, coord):
        return all(a <= v < b for a,v,b in zip(self.mins, coord, self.maxs))

    @abc.abstractmethod
    def path(self, start, end):
        pass


class MeshLeaf(Mesh):

    def __init__(self, dimensions, corner):
        Mesh.__init__(self, dimensions, corner)

        self.nav_graph = {} # {coord -> set(coords)} # navigable
        self.zones = {}
        self.links = {}
        self.paths = {}

    def neighbors(self, coord):
        return cardinal_neighbors(coord) & set(self.nav_graph.keys())

    def cost(self, coord_1, coord_2):
        return 1  # stub.

    ####################################

    def passable(self, coord):
        return coord in self.nav_graph

    def path(self, start, end):
        return my_a_star(self, start, end)

    def calculate_zones(self):

        # if not self.nav_graph:
        #     return
        
        # start = min(self.nav_graph)

        raise NotImplementedError()

    def calculate_links(self):
        raise NotImplementedError()



m = MeshLeaf((10,10), (0,0))
m.navigable = set((x,y) for x in xrange(10) for y in xrange(10)) - set([
    (1, 7), (1, 8), (2, 7), (2, 8), (3, 7), (3, 8),

    (3, 4), (3, 5), (4, 1), (4, 2),
    (4, 3), (4, 4), (4, 5), (4, 6),
    (4, 7), (4, 8), (5, 1), (5, 2),
    (5, 3), (5, 4), (5, 5), (5, 6),
    (5, 7), (5, 8), (6, 2), (6, 3),
    (6, 4), (6, 5), (6, 6), (6, 7),
    (7, 3), (7, 4), (7, 5)
])

print m.navigable

print m.contains((0,0))
print m.contains((3,7))
print m.contains((9,9))
print m.contains((10,10))
print m.contains((3,17))
print m.contains((-5,0))

t0 = time.time()
# out = my_a_star(m, (2,4), (8,5))
out = m.path((2,4), (8,5))
t1 = time.time()
print t1-t0
print

if not out:
    print "No path!"
else:
    print list(out)
