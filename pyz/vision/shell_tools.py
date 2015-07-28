
import itertools

####################################

def plusAndMinusPermutations(items):
    for p in itertools.permutations(items):
        for signs in itertools.product([-1,1], repeat=len(items)):
            yield tuple(a*sign for a,sign in zip(p,signs))

def shell_coords(min_dist, max_dist, dimensions=2):
    """
    DOES NOT INCLUDE MIN (0,0) !!!

    We don't care about the origin.
    """

    if min_dist <= max_dist <= 0:
        return set()

    assert type(min_dist) is int
    assert type(max_dist) is int
    assert min_dist >= 0
    assert max_dist > min_dist

    # the idea:
    #   min_dist < sqrt(a^2 + b^2) <= max_dist

    high_bound = max_dist ** 2
    low_bound  = min_dist ** 2

    possible_not_max = xrange(max_dist)  # UP TO (but not including) MAX_DIST

    pow_sum_op = lambda p: sum(map(lambda n:n**2, p))

    found = set()

    # for example, for 2...3, we're going to loop through 0,1,2 to go next to a 2.
    # anything next to a 3 has to be 0, so we'll ignore that last loop op.

    # UP TO (but not including) MAX_DIST
    # don't repeat things like (0,1) and (1,0), as we'll make these anyways when we permute

    for rest in itertools.combinations(possible_not_max, dimensions-1):
        
        # don't bother unless you hit the minimum
        # don't include the high bound
        for i in xrange(int(min_dist/1.5), max_dist):  # /sqrt(2), really.

            tup = rest + (i,)

            pow_sum = pow_sum_op(tup)

            if not low_bound < pow_sum <= high_bound:  # WE DONT INCLUDE LOW BOUND!
                continue

            every = list(itertools.permutations(tup))

            found.update(every)

    # manually add the max coord
    max_coord = (0,) * (dimensions-1) + (max_dist,)
    every = itertools.permutations(max_coord)
    found.update(every)

    newfound = set()

    # I hate this, but it works simply.
    for each in found:

        for new in plusAndMinusPermutations(each):

            newfound.add(new)

    return newfound


def shell_wrap(n, dimensions=2):
    return shell_coords(n-1, n, dimensions=dimensions)
