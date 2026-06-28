import math
import random
import time
import heapq
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Set, Any

from game_models import Position, INF, EMPTY, GridMap, MapColoringCSP, TicTacToe


@dataclass
class SearchResult:
    path: Optional[List[Position]]
    cost: float
    expanded: int
    runtime: float
    visited_order: List[Position]


def reconstruct_path(parent: Dict[Position, Optional[Position]], goal: Position) -> List[Position]:
    path: List[Position] = []
    cur: Optional[Position] = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return path


def path_cost(grid: GridMap, path: Optional[List[Position]]) -> float:
    if not path:
        return INF
    return sum(grid.cost(p) for p in path[1:])


def manhattan(a: Position, b: Position) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def generate_maze_dfs(rows: int, cols: int, seed: int):
    """Recursive-backtracker DFS maze generation. rows/cols should be odd."""
    random.seed(seed)
    grid = [["#"] * cols for _ in range(rows)]
    visited_order: List[Position] = []
    grid[1][1] = "."
    stack: List[Position] = [(1, 1)]
    while stack:
        r, c = stack[-1]
        visited_order.append((r, c))
        nbrs = []
        for dr, dc in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            nr, nc = r + dr, c + dc
            if 1 <= nr < rows - 1 and 1 <= nc < cols - 1 and grid[nr][nc] == "#":
                nbrs.append((nr, nc, dr, dc))
        if nbrs:
            nr, nc, dr, dc = random.choice(nbrs)
            grid[r + dr // 2][c + dc // 2] = "."
            grid[nr][nc] = "."
            stack.append((nr, nc))
        else:
            stack.pop()
    return grid, visited_order


def bfs_distance_field(grid: GridMap, source: Position) -> Dict[Position, int]:
    """Breadth-first flood fill: shortest step-distance from source to every cell."""
    dist = {source: 0}
    q = deque([source])
    while q:
        cur = q.popleft()
        for nb in grid.neighbors(cur):
            if nb not in dist:
                dist[nb] = dist[cur] + 1
                q.append(nb)
    return dist


def greedy_best_first_search(grid: GridMap, start: Position, goal: Position) -> SearchResult:
    t0 = time.perf_counter()
    frontier: List[Tuple[int, int, Position]] = []
    counter = 0
    heapq.heappush(frontier, (manhattan(start, goal), counter, start))
    parent: Dict[Position, Optional[Position]] = {start: None}
    visited: Set[Position] = set()
    order: List[Position] = []
    expanded = 0
    while frontier:
        _, _, cur = heapq.heappop(frontier)
        if cur in visited:
            continue
        visited.add(cur)
        order.append(cur)
        expanded += 1
        if cur == goal:
            p = reconstruct_path(parent, goal)
            return SearchResult(p, path_cost(grid, p), expanded, time.perf_counter() - t0, order)
        for nb in grid.neighbors(cur):
            if nb not in visited and nb not in parent:
                parent[nb] = cur
                counter += 1
                heapq.heappush(frontier, (manhattan(nb, goal), counter, nb))
    return SearchResult(None, INF, expanded, time.perf_counter() - t0, order)


def astar(grid: GridMap, start: Position, goal: Position) -> SearchResult:
    t0 = time.perf_counter()
    frontier: List[Tuple[float, int, Position]] = []
    counter = 0
    heapq.heappush(frontier, (manhattan(start, goal), counter, start))
    parent: Dict[Position, Optional[Position]] = {start: None}
    g: Dict[Position, float] = {start: 0}
    closed: Set[Position] = set()
    order: List[Position] = []
    expanded = 0
    while frontier:
        _, _, cur = heapq.heappop(frontier)
        if cur in closed:
            continue
        closed.add(cur)
        order.append(cur)
        expanded += 1
        if cur == goal:
            p = reconstruct_path(parent, goal)
            return SearchResult(p, g[goal], expanded, time.perf_counter() - t0, order)
        for nb in grid.neighbors(cur):
            ng = g[cur] + grid.cost(nb)
            if ng < g.get(nb, INF):
                g[nb] = ng
                parent[nb] = cur
                counter += 1
                heapq.heappush(frontier, (ng + manhattan(nb, goal), counter, nb))
    return SearchResult(None, INF, expanded, time.perf_counter() - t0, order)


def next_step_astar(grid: GridMap, src: Position, dst: Position) -> Position:
    res = astar(grid, src, dst)
    if res.path and len(res.path) > 1:
        return res.path[1]
    return src


def next_step_greedy(grid: GridMap, src: Position, dst: Position) -> Position:
    res = greedy_best_first_search(grid, src, dst)
    if res.path and len(res.path) > 1:
        return res.path[1]
    return src


_astar_cache: Dict[Tuple[Position, Position], float] = {}


def clear_astar_cache():
    _astar_cache.clear()


def shortest_cost_between(grid: GridMap, a: Position, b: Position) -> float:
    key = (a, b)
    if key in _astar_cache:
        return _astar_cache[key]
    res = astar(grid, a, b)
    c = res.cost if res.path else INF
    _astar_cache[key] = c
    return c


def route_cost(grid: GridMap, start: Position, items: List[Position], goal: Position, order: List[int]) -> float:
    pts = [start] + [items[i] for i in order] + [goal]
    total = 0.0
    for i in range(len(pts) - 1):
        c = shortest_cost_between(grid, pts[i], pts[i + 1])
        if c == INF:
            return INF
        total += c
    return total


def swap_neighbors(order: List[int]) -> List[List[int]]:
    out = []
    for i in range(len(order)):
        for j in range(i + 1, len(order)):
            n = order[:]
            n[i], n[j] = n[j], n[i]
            out.append(n)
    return out


def steepest_ascent_hill_climbing(grid, start, items, goal, initial_order, max_iterations=100):
    cur = initial_order[:]
    cur_cost = route_cost(grid, start, items, goal, cur)
    for _ in range(max_iterations):
        best, best_cost = cur, cur_cost
        for nb in swap_neighbors(cur):
            c = route_cost(grid, start, items, goal, nb)
            if c < best_cost:
                best, best_cost = nb, c
        if best_cost >= cur_cost:
            break
        cur, cur_cost = best, best_cost
    return {"best_order": cur, "best_cost": cur_cost}


def simple_hill_climbing(grid, start, items, goal, initial_order, max_iterations=100):
    cur = initial_order[:]
    cur_cost = route_cost(grid, start, items, goal, cur)
    for _ in range(max_iterations):
        improved = False
        for nb in swap_neighbors(cur):
            c = route_cost(grid, start, items, goal, nb)
            if c < cur_cost:
                cur, cur_cost = nb, c
                improved = True
                break
        if not improved:
            break
    return {"best_order": cur, "best_cost": cur_cost}




def is_consistent(csp: MapColoringCSP, var: str, value: str, assignment: Dict[str, str]) -> bool:
    return all(assignment.get(n) != value for n in csp.neighbors[var])


def select_unassigned_variable(variables: List[str], assignment: Dict[str, str], domains: Dict[str, Set[str]]) -> str:
    un = [v for v in variables if v not in assignment]
    return min(un, key=lambda v: len(domains[v]))


def backtracking_search(csp: MapColoringCSP, domains: Optional[Dict[str, Set[str]]] = None) -> Tuple[Optional[Dict[str, str]], Dict[str, int]]:
    if domains is None:
        domains = {v: set(s) for v, s in csp.domains.items()}
    metrics = {"assignments_tried": 0, "backtracks": 0}

    def backtrack(assignment: Dict[str, str]) -> Optional[Dict[str, str]]:
        if len(assignment) == len(csp.variables):
            return assignment.copy()
        var = select_unassigned_variable(csp.variables, assignment, domains)
        for value in sorted(domains[var]):
            metrics["assignments_tried"] += 1
            if is_consistent(csp, var, value, assignment):
                assignment[var] = value
                res = backtrack(assignment)
                if res is not None:
                    return res
                del assignment[var]
        metrics["backtracks"] += 1
        return None

    return backtrack({}), metrics


def min_conflicts(csp: MapColoringCSP, max_steps: int = 100) -> Tuple[Optional[Dict[str, str]], Dict[str, int]]:
    metrics = {"steps": 0, "conflicts_resolved": 0}
    
    for restart in range(10):
        current = {}
        for var in csp.variables:
            domain_list = list(csp.domains[var])
            current[var] = random.choice(domain_list)
            
        def conflicts(var: str, val: str, assignment: Dict[str, str]) -> int:
            count = 0
            for n in csp.neighbors[var]:
                if assignment.get(n) == val:
                    count += 1
            return count

        for step in range(max_steps):
            metrics["steps"] += 1
            
            conflicted = []
            for var in csp.variables:
                if any(current[var] == current[n] for n in csp.neighbors[var]):
                    conflicted.append(var)
                    
            if not conflicted:
                return current, metrics
                
            mutable_conflicted = [v for v in conflicted if len(csp.domains[v]) > 1]
            if not mutable_conflicted:
                break
                
            var = random.choice(mutable_conflicted)
            domain_list = list(csp.domains[var])
            
            best_vals = []
            min_c = INF
            for val in domain_list:
                c = conflicts(var, val, current)
                if c < min_c:
                    min_c = c
                    best_vals = [val]
                elif c == min_c:
                    best_vals.append(val)
                    
            val = random.choice(best_vals)
            if current[var] != val:
                current[var] = val
                metrics["conflicts_resolved"] += 1
                
    return None, metrics


def minimax(game: TicTacToe, maximizing: bool, metrics: Dict[str, int]) -> int:
    metrics["nodes"] += 1
    if game.terminal():
        return game.utility()
    if maximizing:
        best = -INF
        for m in game.available_moves():
            game.board[m] = "O"
            best = max(best, minimax(game, False, metrics))
            game.board[m] = EMPTY
        return int(best)
    best = INF
    for m in game.available_moves():
        game.board[m] = "X"
        best = min(best, minimax(game, True, metrics))
        game.board[m] = EMPTY
    return int(best)


def best_move_minimax(game: TicTacToe) -> Tuple[int, int, Dict[str, int]]:
    metrics = {"nodes": 0}
    best_v, best_m = -INF, -1
    for m in game.available_moves():
        game.board[m] = "O"
        v = minimax(game, False, metrics)
        game.board[m] = EMPTY
        if v > best_v:
            best_v, best_m = v, m
    return best_m, int(best_v), metrics


def alpha_beta(game: TicTacToe, maximizing: bool, alpha: float, beta: float, metrics: Dict[str, int]) -> int:
    metrics["nodes"] += 1
    if game.terminal():
        return game.utility()
    if maximizing:
        v = -INF
        for m in game.available_moves():
            game.board[m] = "O"
            v = max(v, alpha_beta(game, False, alpha, beta, metrics))
            game.board[m] = EMPTY
            alpha = max(alpha, v)
            if alpha >= beta:
                metrics["prunes"] += 1
                break
        return int(v)
    v = INF
    for m in game.available_moves():
        game.board[m] = "X"
        v = min(v, alpha_beta(game, True, alpha, beta, metrics))
        game.board[m] = EMPTY
        beta = min(beta, v)
        if alpha >= beta:
            metrics["prunes"] += 1
            break
    return int(v)


def best_move_alpha_beta(game: TicTacToe) -> Tuple[int, int, Dict[str, int]]:
    metrics = {"nodes": 0, "prunes": 0}
    best_v, best_m = -INF, -1
    alpha, beta = -INF, INF
    for m in game.available_moves():
        game.board[m] = "O"
        v = alpha_beta(game, False, alpha, beta, metrics)
        game.board[m] = EMPTY
        if v > best_v:
            best_v, best_m = v, m
        alpha = max(alpha, best_v)
    return best_m, int(best_v), metrics

def and_or_graph_search(grid: GridMap, start: Position, goal: Position) -> Optional[Dict]:
    action_dirs = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}

    max_depth = max(200, grid.height * grid.width)

    def or_search(state: Position, path: List[Position]) -> Optional[Dict]:
        if state == goal:
            return {}
        if len(path) > max_depth or state in path:
            return None
            
        new_path = path + [state]
        
        actions_list = list(action_dirs.keys())
        def action_priority(act):
            dr, dc = action_dirs[act]
            nxt = (state[0] + dr, state[1] + dc)
            if not grid.passable(nxt):
                return INF
            return manhattan(nxt, goal)
            
        actions_list.sort(key=action_priority)
        
        for action in actions_list:
            dr, dc = action_dirs[action]
            nxt = (state[0] + dr, state[1] + dc)
            if not grid.passable(nxt) or nxt in path:
                continue
                
            outcomes = [nxt]
            if grid.cell(state) == "I":
                for nb in grid.neighbors(state):
                    if nb != nxt and nb != state and grid.passable(nb):
                        outcomes.append(nb)
                        
            plan = and_search(state, action, outcomes, new_path)
            if plan is not None:
                return {action: plan}
                
        return None

    def and_search(state: Position, action: str, outcomes: List[Position], path: List[Position]) -> Optional[Dict]:
        plan = {}
        for outcome in outcomes:
            if not grid.passable(outcome):
                return None
            if outcome in path:
                plan[outcome] = {"LOOP": True}  # Trượt về ô cũ trong lộ trình
            else:
                outcome_plan = or_search(outcome, path)
                if outcome_plan is None:
                    return None
                plan[outcome] = outcome_plan
        return plan

    return or_search(start, [])


@dataclass
class StalkerBeliefConfig:
    smell_range: int = 3
    initial_uncertainty: int = 1


class StalkerBeliefTracker:
    """
    Belief State cho Stalker săn Robot.
    Công thức: b' = {s' | ∃s∈b: s' = RESULT(s, a) ∧ OBSERVATION(s') = o}
    """
    
    def __init__(self, config: StalkerBeliefConfig = None):
        self.config = config or StalkerBeliefConfig()
    
    def predict(self, belief: Set[Tuple[int, int]], grid: Any) -> Set[Tuple[int, int]]:
        """Robot di chuyển → belief MỞ RỘNG"""
        new_belief = set()
        for (r, c) in belief:
            new_belief.add((r, c))  # Đứng yên
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if self._is_valid_position(nr, nc, grid):
                    new_belief.add((nr, nc))
        return new_belief
    
    def observe(self, belief: Set[Tuple[int, int]], 
                stalker_pos: Tuple[int, int], 
                robot_actual_pos: Tuple[int, int],
                grid: Any) -> Tuple[Set[Tuple[int, int]], str]:
        """Stalker ngửi → belief THU HẸP"""
        distance = abs(robot_actual_pos[0] - stalker_pos[0]) + \
                   abs(robot_actual_pos[1] - stalker_pos[1])
        
        sensor_reading = 'smelled' if distance <= self.config.smell_range else 'no_smell'
        
        new_belief = set()
        for (r, c) in belief:
            dist_to_stalker = abs(r - stalker_pos[0]) + abs(c - stalker_pos[1])
            
            if sensor_reading == 'smelled':
                if dist_to_stalker <= self.config.smell_range:
                    new_belief.add((r, c))
            else:
                if dist_to_stalker > self.config.smell_range:
                    new_belief.add((r, c))
        
        if not new_belief:
            new_belief = belief.copy()
        
        return new_belief, sensor_reading
    
    def update(self, belief: Set[Tuple[int, int]], 
               stalker_pos: Tuple[int, int],
               robot_actual_pos: Tuple[int, int],
               grid: Any) -> Tuple[Set[Tuple[int, int]], str, dict]:
        """Hàm chính: PREDICT + OBSERVE"""
        belief_after_predict = self.predict(belief, grid)
        new_belief, reading = self.observe(
            belief_after_predict, stalker_pos, robot_actual_pos, grid
        )
        
        metrics = {
            'before_predict': len(belief),
            'after_predict': len(belief_after_predict),
            'after_observe': len(new_belief),
            'sensor_reading': reading,
            'uncertainty_reduction': len(belief) - len(new_belief)
        }
        
        return new_belief, reading, metrics
    
    def _is_valid_position(self, r: int, c: int, grid: Any) -> bool:
        if hasattr(grid, 'passable'):
            return grid.passable((r, c))
        if hasattr(grid, 'grid'):
            grid = grid.grid
        if not (0 <= r < len(grid) and 0 <= c < len(grid[0])):
            return False
        return grid[r][c] != '#'


def initialize_stalker_belief(grid: Any, 
                               exclude_positions: Set[Tuple[int, int]] = None) -> Set[Tuple[int, int]]:
    """Khởi tạo belief ban đầu: tất cả ô hợp lệ đều có thể chứa Robot"""
    belief = set()
    if hasattr(grid, 'grid'):
        grid = grid.grid
    if isinstance(grid, GridMap):
        for r in range(grid.height):
            for c in range(grid.width):
                if grid.passable((r, c)):
                    if exclude_positions is None or (r, c) not in exclude_positions:
                        belief.add((r, c))
    else:
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if grid[r][c] != '#':
                    if exclude_positions is None or (r, c) not in exclude_positions:
                        belief.add((r, c))
    return belief



