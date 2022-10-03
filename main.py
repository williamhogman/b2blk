import math
import random

import pyxel
from si_prefix import si_format

SCREEN_WIDTH = 256
SCREEN_HEIGHT = 256

from si_prefix import si_format

COLORS = [1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 14, 15]

def format_text(v):
    val = 2 ** v
    s = str(val)
    if len(s) > 4:
        return si_format(val)
    return s

class Box:
    SIZE = 32
    PADDING = 4
    SIZE_WITH_PADDING = SIZE + PADDING * 2

    def __repr__(self):
        return f"Box({self.col}, {self.row}, {self.content})"

    @property
    def colrow(self):
        return self.col, self.row

    def __init__(self, col, row):
        self.row = row
        self.col = col
        self.x = self.PADDING + col * self.SIZE_WITH_PADDING
        self.y = self.PADDING + row * self.SIZE_WITH_PADDING
        self.bounding_box = ((self.x, self.y), (self.x + Box.SIZE, self.y + Box.SIZE))
        self.content = 0

    @property
    def color(self):
        if self.content == 0:
            return 13
        return COLORS[self.content % len(COLORS)]

    def may_add_box(self, other):
        if self.content == 0 or other.content == 0:
            return False
        if self.content == other.content:
            return True
        return False
    
    def place(self, val):
        assert self.content == 0
        self.content = val
    
    def add_boxes(self, others):
        self.content += len(others)
        for other in others:
            other.content = 0


    @property
    def text(self):
        val = 2 ** self.content
        s = str(val)
        if len(s) > 4:
            return si_format(val)
        return s

    @property
    def empty(self):
        return self.content == 0

import itertools


class Grid:
    def __init__(self):
        self.cols = []
        self.to_place = 1
        for c in range(4):
            col = []
            for r in range(6):
                col.append(Box(c, r))
            self.cols.append(col)
        self.rows = list(zip(*self.cols))
        self.boxes = list(itertools.chain(*self.cols))

    def block_range(self):
        hi = max(b.content for b in self.boxes if not b.empty)
        lo = hi - 5
        mini = max(lo, 1)
        maxi = hi 
        return mini, max(maxi - 1, 1)

    def score(self):
        return sum(b.content for b in self.boxes)

    def update_to_place(self):
        mini, maxi = self.block_range()
        for b in self.boxes:
            if b.content != 0 and b.content < mini:
                b.content = 0
        boost = (1 / (maxi + 1 / (1 + self.score()))) / 2
        val = min(max(math.floor(mini + random.lognormvariate(0, boost)), 1), maxi)
        self.to_place = val

    def place_block_in_col(self, col):
        block = self.to_place
        for i, box in enumerate(self.cols[col]):
            if box.empty:
                if i > 0 and self.cols[col][i - 1].may_add_box(box):
                    box.content += 1
                    return col, i -1
                else:
                    box.place(self.to_place)
                    self.update_to_place()
                return col, i
        if self.cols[col][-1].content == block:
            self.cols[col][-1].content += 1
            self.update_to_place()
            return col, len(self.cols[col]) - 1

        return None

    def reachability(self, coord):
        col, row = coord
        range(len(row))
        range(len(col))
        len(col)

    NEIGHBOUR_COORDS = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
    ]
    def neighbours(self, colrow):
        col, row = colrow
        for (id, jd) in self.NEIGHBOUR_COORDS:
            new_col = col + id
            new_row = row + jd
            if new_col < 0 or new_col >= len(self.cols):
                continue
            if new_row < 0 or new_row >= len(self.rows):
                continue
            yield new_col, new_row
    def bfs(self, center):
        queue = [center.colrow]
        visited = set()
        val = center.content
        output = []
        while len(queue) > 0:
            current = queue.pop(0)
            visited.add(current)
            matches = [(c, r) for (c, r) in self.neighbours(current) if (c, r) not in visited and self.cols[c][r].content == val]
            queue.extend(matches)
            output.extend(matches)
        return output


    def compress_grid(self, center):
        same_col = self.cols[center[0]]
        same_row = self.rows[center[1]]
        centers = itertools.chain([center], (c.colrow for c in same_col if not c.empty), (c.colrow for c in same_row if not c.empty), (c.colrow for c in self.boxes if not c.empty))
        for (col, row) in centers:
            b = self.cols[col][row]
            if b.content == 0:
                continue
            res = self.bfs(b)
            if len(res) > 0:
                found_boxes = list(self.cols[c][r] for (c, r) in res)
                found_boxes.append(b)
                found_boxes.sort(key=lambda b: b.row)
                for b2 in found_boxes:
                    if b.col == b2.col and b2.row <= b.row:
                        b2.add_boxes([fb for fb in found_boxes if fb is not b2])
                        return res
        return []

    def fall_col(self, center, did_recur=False):
        col, row = center
        c = self.cols[col]
        for i in range(len(c) - 1, 0, -1):
            a = c[i]
            b = c[i - 1]
            if b.empty and not a.empty:
                b.place(a.content)
                a.content = 0
                return (col, row)
        if not did_recur:
            for i in range(len(self.cols)):
                self.fall_col((i, 0), True)



KEY_MAP = {pyxel.KEY_1: 0, pyxel.KEY_2: 1, pyxel.KEY_3: 2, pyxel.KEY_4: 3}

FALL = 0
COMPRESS = 1

class OpStack:
    def __init__(self):
        self.stack = []
    
    def has(self, type=None):
        has_stack = len(self.stack) > 0
        if type is None:
            return has_stack
        return has_stack and self.stack[-1][0] == type

    def push_fall(self, coord):
        if coord is not None:
            self.stack.append((FALL, coord))

    def push_compress(self, coord):
        if coord is not None:
            self.stack.append((COMPRESS, coord))

    def push_both(self, coord):
        self.push_fall(coord)
        self.push_compress(coord)

    def pop_compress(self):
        if self.has(COMPRESS):
            return self.stack.pop()[1]
    
    def pop_fall(self):
        if self.has(FALL):
            return self.stack.pop()[1]
        

class App:
    def __init__(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Pyxel Bubbles", capture_scale=1)
        pyxel.mouse(True)
        self.grid = Grid()
        self.compress_at = None
        self.fall = None
        self.op_stack = OpStack()
        pyxel.run(self.update, self.draw)
        

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        if (ca := self.op_stack.pop_compress()) is not None:
            for x in self.grid.compress_grid(ca):
                self.op_stack.push_both(x)
        elif (fa := self.op_stack.pop_fall()) is not None:
            self.op_stack.push_both(self.grid.fall_col(fa))
        else:
            for k, v in KEY_MAP.items():
                if pyxel.btnp(k):
                    self.op_stack.push_both(self.grid.place_block_in_col(v))
    def draw(self):
        pyxel.cls(7)
        pyxel.text(168, 16, f"Score: {format_text(self.grid.score())}", 0)
        pyxel.text(168, 32, f"Next up: {format_text(self.grid.to_place)}", 0)
        for box in self.grid.boxes:
            pyxel.rect(box.x, box.y, Box.SIZE, Box.SIZE, box.color)
            if box.content > 0:
                t = box.text
                tl = len(t)
                pyxel.text((box.x + Box.SIZE // 2) - (tl//2) * 4, (box.y + Box.SIZE // 2) - 8, t, 7)


App()
