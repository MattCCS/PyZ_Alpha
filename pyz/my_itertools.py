
def islice_fixed(it, cap=-1, fill=None):
    it = iter(it)

    if cap < 0:
        while True:
            try:
                yield next(it)
            except StopIteration:
                return
    else:
        for i in xrange(cap):
            try:
                yield next(it)
            except StopIteration:
                yield fill


def yield_parallel(*its):
    done_so_far = 0

    its = (iter(it) for it in its)

    for it in its:

        # deplete first N from each iterator
        for _ in xrange(done_so_far):
            try:
                next(it)
            except StopIteration:
                break

        for elem in it:
            yield elem
            done_so_far += 1