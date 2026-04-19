class Board:
    DIRECTIONS = [(-1, -1), (-1, 1), (0, -2), (0, 2), (1, -1), (1, 1)]
    _TRIANGLE_BOUNDS = {'N': {0: (12, 12), 1: (11, 13), 2: (10, 14), 3: (9, 15)}, 'S': {13: (9, 15), 14: (10, 14), 15: (11, 13), 16: (12, 12)}, 'NW': {4: (0, 6), 5: (1, 5), 6: (2, 4), 7: (3, 3)}, 'NE': {4: (18, 24), 5: (19, 23), 6: (20, 22), 7: (21, 21)}, 'SW': {9: (3, 3), 10: (2, 4), 11: (1, 5), 12: (0, 6)}, 'SE': {9: (21, 21), 10: (20, 22), 11: (19, 23), 12: (18, 24)}}
    OPPOSITE = {'N': 'S', 'S': 'N', 'NE': 'SW', 'SW': 'NE', 'NW': 'SE', 'SE': 'NW'}

    def __init__(self):
        self._init_positions()
        self._init_triangles()
        self.grid = {pos: None for pos in self.all_positions}

    def _init_positions(self):
        self.row_cols = {0: [12], 1: [11, 13], 2: [10, 12, 14], 3: [9, 11, 13, 15], 4: list(range(0, 25, 2)), 5: list(range(1, 24, 2)), 6: list(range(2, 23, 2)), 7: list(range(3, 22, 2)), 8: list(range(4, 21, 2)), 9: list(range(3, 22, 2)), 10: list(range(2, 23, 2)), 11: list(range(1, 24, 2)), 12: list(range(0, 25, 2)), 13: [9, 11, 13, 15], 14: [10, 12, 14], 15: [11, 13], 16: [12]}
        self.all_positions = set()
        for (r, cols) in self.row_cols.items():
            for c in cols:
                self.all_positions.add((r, c))

    def _init_triangles(self):
        self.triangles = {}
        for (name, bounds) in self._TRIANGLE_BOUNDS.items():
            positions = set()
            for (r, (lo, hi)) in bounds.items():
                for c in self.row_cols[r]:
                    if lo <= c <= hi:
                        positions.add((r, c))
            self.triangles[name] = positions

    def is_valid(self, pos):
        return pos in self.all_positions

    def get_triangle(self, pos):
        for (name, positions) in self.triangles.items():
            if pos in positions:
                return name
        return None

    def get_simple_moves(self, pos):
        moves = []
        (r, c) = pos
        for (dr, dc) in self.DIRECTIONS:
            (nr, nc) = (r + dr, c + dc)
            if (nr, nc) in self.all_positions and self.grid[nr, nc] is None:
                moves.append((nr, nc))
        return moves

    def get_single_jumps(self, pos):
        jumps = []
        (r, c) = pos
        for (dr, dc) in self.DIRECTIONS:
            (mr, mc) = (r + dr, c + dc)
            (lr, lc) = (r + 2 * dr, c + 2 * dc)
            if (mr, mc) in self.all_positions and self.grid.get((mr, mc)) is not None and ((lr, lc) in self.all_positions) and (self.grid.get((lr, lc)) is None):
                jumps.append((lr, lc))
        return jumps

    def get_all_jump_destinations(self, pos):
        original = self.grid[pos]
        self.grid[pos] = None
        destinations = set()
        self._find_jumps(pos, destinations)
        self.grid[pos] = original
        return destinations

    def _find_jumps(self, pos, visited):
        (r, c) = pos
        for (dr, dc) in self.DIRECTIONS:
            (mr, mc) = (r + dr, c + dc)
            (lr, lc) = (r + 2 * dr, c + 2 * dc)
            if (mr, mc) in self.all_positions and self.grid.get((mr, mc)) is not None and ((lr, lc) in self.all_positions) and (self.grid.get((lr, lc)) is None) and ((lr, lc) not in visited):
                visited.add((lr, lc))
                self._find_jumps((lr, lc), visited)

    def get_all_valid_moves(self, pos, goal_triangle=None):
        simple = self.get_simple_moves(pos)
        jumps = list(self.get_all_jump_destinations(pos))
        all_moves = [m for m in simple + jumps if m != pos]
        if goal_triangle and pos in self.triangles.get(goal_triangle, set()):
            goal_set = self.triangles[goal_triangle]
            all_moves = [m for m in all_moves if m in goal_set]
        return all_moves

    def move_piece(self, from_pos, to_pos):
        self.grid[to_pos] = self.grid[from_pos]
        self.grid[from_pos] = None

    def setup_pieces(self, player_id, triangle_name):
        for pos in self.triangles[triangle_name]:
            self.grid[pos] = player_id

    def clear(self):
        for pos in self.all_positions:
            self.grid[pos] = None

    @staticmethod
    def is_jump(from_pos, to_pos):
        dr = abs(to_pos[0] - from_pos[0])
        dc = abs(to_pos[1] - from_pos[1])
        return (dr, dc) in [(2, 2), (0, 4)]