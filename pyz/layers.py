
import settings

import itertools


def islice_fixed(it, cap=-1, fill=None):

    # no cap
    if cap < 0:
        for elem in it:
            yield elem
        return

    # cap is 0
    if cap == 0:
        return

    # try to hit cap
    i = 0
    for (i, elem) in enumerate(it, 1):
        yield elem
        if i == cap:
            return

    # add filler
    remaining = cap - i
    for _ in xrange(remaining):
        yield fill


def yield_parallel(*its):
    count = 0

    its = map(iter, its)

    for it in its:

        # deplete first N from each iterator
        for _ in xrange(count):
            try:
                next(it)
            except StopIteration:
                break

        for elem in it:
            yield elem
            count += 1

####################################

class Layer(object):
    
    def __init__(self, dims=(settings.WIDTH, settings.HEIGHT)):
        self.w, self.h = dims

        self.arr = [None] * self.w * self.h

    def size(self):
        return self.w * self.h

    def convert_to_1d(self, x, y):
        return self.w * y + x

    # setting points/ranges
    def set(self, x, y, char=None):
        """None is transparent"""
        self.seti(self.convert_to_1d(x,y), char)

    def seti(self, i, char=None):
        """None is transparent"""
        assert char is None or len(char) == 1
        self.arr[i] = char

    def setrange(self, x, y, it):
        self.setrangei(self.convert_to_1d(x,y), it)

    def setrangei(self, i, it):
        for (idx, c) in enumerate(it, i):
            try:
                self.seti(idx, c)
            except IndexError:  # out of bounds (either direction)
                if idx >= self.size():
                    break   # beyond size -- don't bother

    def setlines(self, x, y, lines):
        for (i,line) in enumerate(lines):
            self.setrange(x, y+i, line)

    ####################################
    # faster, dangerous methods

    def _setrangefast(self, x, y, it):
        self._setrangeifast(self.convert_to_1d(x,y), it)

    def _setrangeifast(self, i, it):
        assert i >= 0  # i must be in [0, self.size()]
        rem = self.size() - i
        self.arr[i:] = islice_fixed(yield_parallel(it, self.arr[i:]), rem)

    # iterating over lines
    def __iter__(self):
        for y in xrange(self.h):
            start = self.w * y
            yield self.arr[start:start + self.w]

    # rendering
    def debugrender(self):
        return '\n'.join(''.join((e if e is not None else ' ') for e in row) for row in self)

    def renderto(self, screen):
        raise NotImplementedError()


class LayerManager(object):

    def __init__(self, dims=(settings.WIDTH, settings.HEIGHT)):
        self.w, self.h = dims

        self.layers = []
        self.layermap = {}

    def get(self, name):
        return self.layermap[name]

    def render(self):
        pass


BODY = """\
 /-\\ 
 \\_/ 
 -o-
/ | \\
  o
 / \\
 | |""".split('\n')


if __name__ == '__main__':
    l = Layer((16,12))
    l.setrange(3,3,'hello!  there once was a man from bristol')
    l.set(5,3, 'X')
    l.setlines(3,4, BODY)
    # l.setrangei(l.size()-5, ['a', 'b', None])
    l._setrangeifast(l.size()-5, 'ab')
    print l.debugrender()

    print list(islice_fixed('', 5))
    print list(islice_fixed('abc', 5))
    print list(islice_fixed('abcdefg', 5))
    print list(islice_fixed('abc', 0))

    print list(yield_parallel('123','abcd','boo'))
