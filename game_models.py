from typing import Tuple, List, Optional, Dict, Set

Position = Tuple[int, int]
INF = float("inf")
EMPTY = " "

class GridMap:
    COSTS = {".": 1, "M": 3}

    def __init__(self, rows: List[str]):
        self.rows = rows
        self.height = len(rows)
        self.width = len(rows[0]) if rows else 0

    def in_bounds(self, pos: Position) -> bool:
        r, c = pos
        return 0 <= r < self.height and 0 <= c < self.width

    def cell(self, pos: Position) -> str:
        r, c = pos
        return self.rows[r][c]

    def passable(self, pos: Position) -> bool:
        return self.in_bounds(pos) and self.cell(pos) != "#"

    def cost(self, pos: Position) -> int:
        return self.COSTS.get(self.cell(pos), 1)

    def neighbors(self, pos: Position) -> List[Position]:
        r, c = pos
        cand = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
        return [p for p in cand if self.passable(p)]

    def find(self, symbol: str) -> Optional[Position]:
        for r in range(self.height):
            for c in range(self.width):
                if self.rows[r][c] == symbol:
                    return (r, c)
        return None


class MapColoringCSP:
    def __init__(self, variables, neighbors, colors, fixed=None):
        self.variables = variables
        self.neighbors = neighbors
        self.colors = colors
        self.domains = {v: set(colors) for v in variables}
        if fixed:
            for v, col in fixed.items():
                self.domains[v] = {col}

    @staticmethod
    def constraint(a, b):
        return a != b


class TicTacToe:
    WIN_LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6),
                 (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]

    def __init__(self, board=None):
        self.board = board[:] if board else [EMPTY] * 9

    def available_moves(self):
        return [i for i, c in enumerate(self.board) if c == EMPTY]

    def winner(self):
        for a, b, c in self.WIN_LINES:
            if self.board[a] != EMPTY and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a]
        return None

    def is_full(self):
        return EMPTY not in self.board

    def terminal(self):
        return self.winner() is not None or self.is_full()

    def utility(self):
        w = self.winner()
        return 1 if w == "O" else -1 if w == "X" else 0
