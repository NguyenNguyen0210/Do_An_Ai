from __future__ import annotations

import sys
import os
import math
import random
import time
from typing import Dict, List, Tuple, Optional, Set

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QTimer, QRectF

from game_models import Position, INF, EMPTY, GridMap, MapColoringCSP, TicTacToe
from algorithms import (
    generate_maze_dfs,
    bfs_distance_field,
    astar,
    greedy_best_first_search,
    next_step_astar,
    next_step_greedy,
    clear_astar_cache,
    steepest_ascent_hill_climbing,
    simple_hill_climbing,
    backtracking_search,
    min_conflicts,
    best_move_minimax,
    best_move_alpha_beta,
    and_or_graph_search,
    manhattan,
    StalkerBeliefConfig,
    StalkerBeliefTracker,
    initialize_stalker_belief
)


# ============================================================
#  AI MAZE QUEST  -  ALL-IN-ONE GAME (PyQt5)
# ============================================================

class T:
    BG = "#0f1118"
    SIDEBAR = "#161a26"
    PANEL = "#1b2030"
    PANEL_2 = "#232a3d"
    ACCENT = "#5b8cff"
    ACCENT_DIM = "#2f3d6b"
    OK = "#22d3a6"
    WARN = "#ffd166"
    DANGER = "#ff6b6b"
    TEXT = "#e8ebf2"
    MUTED = "#8b93ad"
    WALL = "#2c3350"
    MUD = "#7a5b3a"
    ICE = "#b8e2f2"
    ITEM = "#c792ea"


ZONE_TINT = {"Red": "#241a22", "Green": "#19241f", "Blue": "#1a2030", None: "#141a29"}


# ============================================================
#  QSS (plain string, hardcoded colors, single braces)
# ============================================================

QSS = """
QWidget { background: #0f1118; color: #e8ebf2; font-family: 'Segoe UI', Arial; font-size: 14px; }
#Brand { color: #5b8cff; font-size: 20px; font-weight: bold; letter-spacing: 1px; }
#Subtitle { color: #8b93ad; font-size: 12px; }
#SectionLabel { color: #5b8cff; font-size: 13px; font-weight: bold; letter-spacing: 0.5px; margin-top: 6px; margin-bottom: 2px; }
QTextEdit { background: #1b2030; border: 1px solid #2c3350; border-radius: 8px;
    font-family: Consolas, monospace; font-size: 13px; line-height: 1.4; padding: 6px; }
QPushButton { background: #232a3d; color: #e8ebf2; border: 1px solid #2c3350;
    border-radius: 6px; padding: 8px; font-weight: bold; font-size: 12px; }
QPushButton:hover { background: #2f3d6b; border-color: #5b8cff; }
QToolTip { background-color: #1b2030; color: #e8ebf2; border: 1px solid #5b8cff; border-radius: 6px; padding: 6px; font-family: 'Segoe UI', Arial; font-size: 12px; }
"""


# ============================================================
#  MINIMAP WIDGET
# ============================================================

class MinimapWidget(QtWidgets.QWidget):
    def __init__(self, board, parent=None):
        super().__init__(parent)
        self.board = board
        self.scale = 6
        self.setFixedSize(self.board.cols * self.scale + 4, self.board.rows * self.scale + 4)
        
    def paintEvent(self, event):
        qp = QtGui.QPainter(self)
        qp.setRenderHint(QtGui.QPainter.Antialiasing, False)
        qp.setPen(QtGui.QPen(QtGui.QColor("#5b8cff"), 1))
        qp.setBrush(QtGui.QColor("#161a26"))
        qp.drawRoundedRect(0, 0, self.width() - 1, self.height() - 1, 4, 4)
        
        sc = self.scale
        ox, oy = 2, 2
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                ch = self.board.grid[r][c]
                x, y = ox + c * sc, oy + r * sc
                if ch == "#":
                    col = QtGui.QColor("#2c3350")
                elif ch == "M":
                    col = QtGui.QColor("#7a5b3a")
                elif ch == "I":
                    col = QtGui.QColor("#b8e2f2")
                elif ch == "W":
                    col = QtGui.QColor("#2f6db5")
                else:
                    col = QtGui.QColor("#141a29")
                qp.fillRect(int(x), int(y), int(sc), int(sc), col)
                
        er, ec = self.board.exit
        qp.fillRect(ox + ec * sc, oy + er * sc, sc, sc, QtGui.QColor("#22d3a6"))
        
        for i, s in enumerate(self.board.survivors):
            if i not in self.board.collected:
                qp.fillRect(ox + s[1] * sc, oy + s[0] * sc, sc, sc, QtGui.QColor("#c792ea"))
                
        for g in self.board.guards:
            qp.fillRect(ox + g["pos"][1] * sc, oy + g["pos"][0] * sc, sc, sc, QtGui.QColor(g["color"]))
            
        pr, pc = self.board.player
        qp.fillRect(ox + pc * sc, oy + pr * sc, sc, sc, QtGui.QColor("#5b8cff"))
        qp.end()


# ============================================================
#  GAME BOARD WIDGET
# ============================================================

class BoardWidget(QtWidgets.QWidget):
    logMessage = QtCore.pyqtSignal(str)
    statusChanged = QtCore.pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.rows, self.cols, self.cell = 15, 21, 30
        self.setFixedSize(self.cols * self.cell, self.rows * self.cell)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.grid = [["#"] * self.cols for _ in range(self.rows)]
        self.gm = GridMap(self._rows())
        self.start = (1, 1)
        self.exit = (self.rows - 2, self.cols - 2)
        self.player = self.start
        self.survivors: List[Position] = []
        self.collected: Set[int] = set()
        self.guards: List[dict] = []
        self.dist_field: Dict[Position, int] = {}
        self.zone_solution: Dict[str, str] = {}
        self.suggested_order: List[int] = []
        self.route_cells_sa: List[Position] = []
        self.route_cells_hc: List[Position] = []
        self.sa_cost = 0.0
        self.hc_cost = 0.0
        self.guard_paths: List[Tuple[str, List[Position]]] = []
        self.show_gps_guide = False
        self.hint_uses = 3
        self.lives = 3
        self.belief_state: Set[Position] = set()
        self.fog_traps: List[Position] = []
        self.arrow_pixmap = QtGui.QPixmap("right-arrow.png")
        if not self.arrow_pixmap.isNull():
            self.arrow_pixmap = self.arrow_pixmap.scaled(self.cell - 10, self.cell - 10, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.arrow_pixmap = self.tint_pixmap(self.arrow_pixmap, "#ffd166")
        wall_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "firewall.png")
        self.wall_pixmap = QtGui.QPixmap(wall_path)
        if self.wall_pixmap.isNull():
            self.wall_pixmap = QtGui.QPixmap("firewall.png")
        if not self.wall_pixmap.isNull():
            self.wall_pixmap = self.wall_pixmap.scaled(self.cell, self.cell, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.turn = 0
        self.game_over = False
        self.won = False
        self.message = ""
        self.duel_next = "minimax"
        self.seed = 0
        self.selected_tree_cell = None

    def tint_pixmap(self, pixmap, color):
        if pixmap.isNull():
            return pixmap
        tinted = QtGui.QPixmap(pixmap.size())
        tinted.fill(Qt.transparent)
        painter = QtGui.QPainter(tinted)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), QtGui.QColor(color))
        painter.end()
        return tinted

    def _rows(self):
        return ["".join(r) for r in self.grid]

    def log(self, msg):
        # Color mapping for different AI groups to create syntax highlighting in console log
        color_map = {
            "G1": "#5b8cff",        # DFS, BFS (Neon Blue)
            "G2": "#ffd166",        # A*, Greedy (Warm Yellow)
            "G3": "#c792ea",        # Hill Climbing, Simple Hill Climbing (Light Purple)
            "G4": "#ff8c00",        # Complex Environments
            "G5": "#22d3a6",        # Backtracking, Min-Conflicts CSP (Neon Green)
            "G6": "#ff6b6b",        # Minimax, Alpha-Beta Adversarial (Coral Red)
            "Game": "#a5d6a7",      # Soft Green
            "CSP": "#e57373",       # Pink Red
            "Địa hình": "#ba68c8"   # Magenta
        }
        
        formatted = msg
        # Extract tag and format HTML
        if msg.startswith("[") and "]" in msg:
            idx = msg.find("]")
            tag = msg[1:idx]
            rest = msg[idx+1:]
            
            # Match group color
            color = "#8b93ad" # default gray
            for key, val in color_map.items():
                if tag.startswith(key):
                    color = val
                    break
            formatted = f"<font color='{color}'><b>[{tag}]</b></font><font color='#e8ebf2'>{rest}</font>"
        elif msg.startswith("====="):
            formatted = f"<font color='#5b8cff'><b>{msg}</b></font>"
            
        self.logMessage.emit(formatted)

    # ---- level setup: every algorithm runs at least once here ----
    def new_game(self, seed=None):
        if hasattr(self, "anim_timer") and self.anim_timer.isActive():
            self.anim_timer.stop()
            
        self.seed = seed if seed is not None else random.randint(0, 999999)
        self.turn = 0
        self.game_over = False
        self.won = False
        self.message = ""
        self.collected = set()
        self.duel_next = "minimax"
        self.guard_paths = []
        self.show_gps_guide = False
        self.hint_uses = 3
        self.lives = 3
        self.stalker_belief = set()
        self.fog_traps = []
        self.selected_tree_cell = None
        self.log("===== Màn chơi mới - seed %d =====" % self.seed)

        # 1. Sinh cấu trúc mê cung đích bằng DFS
        final_char_grid, dfs_order = generate_maze_dfs(self.rows, self.cols, self.seed)
        random.seed(self.seed + 99)
        for r in range(1, self.rows - 1):
            for c in range(1, self.cols - 1):
                if final_char_grid[r][c] == "#":
                    if random.random() < 0.15:
                        final_char_grid[r][c] = "."
                        
        self.final_grid = final_char_grid
        
        # Tạo chuỗi thứ tự các ô được đào
        self.carve_sequence = []
        for p in dfs_order:
            if p not in self.carve_sequence and self.final_grid[p[0]][p[1]] != "#":
                self.carve_sequence.append(p)
        for r in range(self.rows):
            for c in range(self.cols):
                if self.final_grid[r][c] != "#" and (r, c) not in self.carve_sequence:
                    self.carve_sequence.append((r, c))
                    
        # Khởi tạo bản đồ FULL TƯỜNG #
        self.grid = [["#"] * self.cols for _ in range(self.rows)]
        self.start = (1, 1)
        self.exit = (self.rows - 2, self.cols - 2)
        self.player = self.start
        
        # Giải CSP tô màu các vùng an toàn ban đầu
        self.solve_zone_csp()
        # Chuẩn bị danh sách các ô địa hình Bùn M và Băng I (chưa sơn ngay)
        self.terrain_sequence = self.compute_terrain()
        
        # Chuẩn bị lịch sử sửa mâu thuẫn Min-Conflicts
        self.min_conflicts_history = self.generate_min_conflicts_history()
        self.zone_solution = self.min_conflicts_history[0] # Khởi tạo bằng bản màu ngẫu nhiên ban đầu
        
        # Chuẩn bị danh sách các ô địa hình Bùn M và Băng I (chưa sơn ngay)
        self.terrain_sequence = self.compute_terrain()
        
        # Trạng thái Animation
        self.anim_state = "FULL_WALLS"
        self.anim_step = 0
        self.latest_carved_pos = None
        
        if not hasattr(self, "anim_timer"):
            self.anim_timer = QtCore.QTimer(self)
            self.anim_timer.timeout.connect(self.advance_maze_animation)
            
        self.anim_timer.start(30)
        self.update()

    def compute_terrain(self):
        random.seed(self.seed + 5)
        floors = [(r, c) for r in range(self.rows) for c in range(self.cols)
                  if self.final_grid[r][c] == "." and (r, c) not in (self.start, self.exit)]
        random.shuffle(floors)
        n_mud = len(floors) // 6
        n_ice = len(floors) // 10
        seq = []
        for (r, c) in floors[:n_mud]:
            seq.append((r, c, "M"))
        for (r, c) in floors[n_mud:n_mud + n_ice]:
            seq.append((r, c, "I"))
        self.log("[Địa hình] Khởi tạo %d ô bùn 🐾 (chi phí 3), %d ô Băng ❄️ (trơn trượt)." % (n_mud, n_ice))
        return seq

    def advance_maze_animation(self):
        if self.anim_state == "FULL_WALLS":
            self.log("[G1-DFS] Khởi tạo mê cung full tường #. Bắt đầu đục tường bằng thuật toán DFS (Recursive Backtracker)...")
            self.anim_state = "CARVING"
            self.anim_step = 0
            self.anim_delay = 0
            return

        elif self.anim_state == "CARVING":
            if self.anim_step < len(self.carve_sequence):
                r, c = self.carve_sequence[self.anim_step]
                self.grid[r][c] = "."
                self.latest_carved_pos = (r, c)
                self.anim_step += 1
                self.update()
            else:
                if getattr(self, "anim_delay", 0) < 10:
                    self.anim_delay = getattr(self, "anim_delay", 0) + 1
                    return
                self.log("[G5-MinConflicts Map Coloring] Đào xong mê cung thô! Bắt đầu trực quan thuật toán Min-Conflicts tô màu 6 phân vùng...")
                self.anim_state = "ZONE_COLORING"
                self.mc_step_idx = 0
                self.mc_sub_delay = 0
                self.anim_delay = 0

        elif self.anim_state == "ZONE_COLORING":
            if getattr(self, "mc_step_idx", 0) < len(self.min_conflicts_history):
                # Trực quan hóa từng bước sửa mâu thuẫn Min-Conflicts chậm rãi (~0.75s bước 1 và ~0.54s các bước sau)
                delay_target = 25 if self.mc_step_idx == 0 else 18
                if getattr(self, "mc_sub_delay", 0) < delay_target:
                    self.mc_sub_delay = getattr(self, "mc_sub_delay", 0) + 1
                    return
                self.mc_sub_delay = 0
                self.zone_solution = self.min_conflicts_history[self.mc_step_idx]
                
                if self.mc_step_idx == 0:
                    self.log("[G5-MinConflicts] BƯỚC 1: Khởi tạo ngẫu nhiên màu cho 6 phân vùng (đang có mâu thuẫn màu giáp ranh)...")
                else:
                    self.log("[G5-MinConflicts] BƯỚC %d: Thuật toán Min-Conflicts đã sửa mâu thuẫn màu giáp ranh giữa các phân vùng." % (self.mc_step_idx + 1))
                    
                self.mc_step_idx += 1
                self.update()
            else:
                if getattr(self, "anim_delay", 0) < 10:
                    self.anim_delay = getattr(self, "anim_delay", 0) + 1
                    return
                self.log("[Địa hình] Bắt đầu trực quan tô màu sơn từng ô Bùn 🐾 và Băng ❄️...")
                self.anim_state = "ZONES"
                self.anim_step = 0
                self.anim_delay = 0
                self.terrain_sub_delay = 0

        elif self.anim_state == "ZONES":
            # Sơn địa hình Bùn M và Băng I chậm rãi từng ô một
            if self.anim_step < len(self.terrain_sequence):
                if getattr(self, "terrain_sub_delay", 0) < 2: # Giữ 2 nhịp (~60ms) mỗi ô địa hình
                    self.terrain_sub_delay = getattr(self, "terrain_sub_delay", 0) + 1
                    return
                self.terrain_sub_delay = 0
                r, c, t_type = self.terrain_sequence[self.anim_step]
                self.grid[r][c] = t_type
                self.latest_carved_pos = (r, c)
                self.anim_step += 1
                self.update()
            else:
                if getattr(self, "anim_delay", 0) < 12:
                    self.anim_delay = getattr(self, "anim_delay", 0) + 1
                    return
                self.gm = GridMap(self._rows())
                self.anim_state = "ENTITIES"
                self.log("[Game] Đang xuất hiện Nạn nhân 🤕, Robot 🤖, Lối ra 🚪 và Các Bảo vệ 👮‍♂️...")
                self.anim_delay = 0

        elif self.anim_state == "ENTITIES":
            self.anim_timer.stop()
            self.anim_state = "IDLE"
            self.latest_carved_pos = None
            
            self.dist_field = bfs_distance_field(self.gm, self.exit)
            d0 = self.dist_field.get(self.start, -1)
            self.log("[G1-BFS] Trường khoảng cách từ lối ra: %d ô tới được, Bắt đầu->Lối ra=%s bước." % (len(self.dist_field), d0))
            
            self.place_survivors()
            self.teleport_cooldown = 0
            self.optimize_route()
            self.spawn_guards()
            self.update_guard_paths()
            self.benchmark_adversarial()
            self.emit_status()
            self.update()

    def add_terrain(self):
        pass



    def zone_of(self, pos):
        r, c = pos
        zr = 0 if r < self.rows // 2 else 1
        third = max(1, self.cols // 3)
        zc = min(2, c // third)
        return zr * 3 + zc

    def zone_tint(self, pos):
        if hasattr(self, "anim_state") and self.anim_state in ("FULL_WALLS", "CARVING"):
            return "#141a29"
        if hasattr(self, "anim_state") and self.anim_state == "ZONE_COLORING":
            z_idx = self.zone_of(pos)
            if hasattr(self, "revealed_zone_count") and z_idx >= self.revealed_zone_count:
                return "#141a29"
        col = self.zone_solution.get("Z%d" % self.zone_of(pos))
        return ZONE_TINT.get(col, "#141a29")

    def generate_min_conflicts_history(self):
        variables = ["Z%d" % i for i in range(6)]
        neighbors = {
            "Z0": ["Z1", "Z3"], "Z1": ["Z0", "Z2", "Z4"], "Z2": ["Z1", "Z5"],
            "Z3": ["Z0", "Z4"], "Z4": ["Z1", "Z3", "Z5"], "Z5": ["Z2", "Z4"],
        }
        colors = ["Red", "Green", "Blue"]
        
        best_history = []
        for attempt in range(50):
            history = []
            random.seed(self.seed + attempt + 10)
            current = {v: random.choice(colors) for v in variables}
            history.append(current.copy())
            
            def get_conflicts(v, val, assign):
                return sum(1 for n in neighbors[v] if assign.get(n) == val)
                
            solved = False
            for step in range(30):
                conflicted = [v for v in variables if any(current[v] == current[n] for n in neighbors[v])]
                if not conflicted:
                    solved = True
                    break
                var = random.choice(conflicted)
                min_c = INF
                best_vals = []
                for val in colors:
                    c = get_conflicts(var, val, current)
                    if c < min_c:
                        min_c = c
                        best_vals = [val]
                    elif c == min_c:
                        best_vals.append(val)
                val = random.choice(best_vals)
                if current[var] != val:
                    current[var] = val
                    history.append(current.copy())
                    
            if solved:
                if len(history) > len(best_history):
                    best_history = history
                if len(history) >= 2:
                    break
                    
        if not best_history:
            best_history = [{v: colors[i % 3] for i, v in enumerate(variables)}]
            
        return best_history

    # [G5 - CSP] color 6 security zones (map coloring)
    def solve_zone_csp(self, use_backtracking=False):
        variables = ["Z%d" % i for i in range(6)]
        neighbors = {
            "Z0": ["Z1", "Z3"], "Z1": ["Z0", "Z2", "Z4"], "Z2": ["Z1", "Z5"],
            "Z3": ["Z0", "Z4"], "Z4": ["Z1", "Z3", "Z5"], "Z5": ["Z2", "Z4"],
        }
        
        if use_backtracking:
            # Khi mất mạng: dùng Backtracking Search khởi tạo lại màu các phân vùng, ép buộc vùng hiện tại của Robot thành Vùng An Toàn (Green)
            player_zone = "Z%d" % self.zone_of(self.player)
            csp = MapColoringCSP(variables, neighbors, ["Red", "Green", "Blue"], fixed={player_zone: "Green"})
            sol, metrics = backtracking_search(csp)
            if sol is None:
                csp = MapColoringCSP(variables, neighbors, ["Red", "Green", "Blue"])
                sol, metrics = backtracking_search(csp)
            self.zone_solution = sol or {}
            self.log("[G5-Backtracking] MẤT 1 MẠNG! Đã chạy Backtracking Search thiết lập Vùng An Toàn Green 🟢 ngay tại ô bạn đang đứng %s (%s): %s | Thử: %d, Quay lui: %d"
                     % (str(self.player), player_zone, sol, metrics["assignments_tried"], metrics["backtracks"]))
        else:
            # Khởi tạo game mới: dùng Min-Conflicts
            history = self.generate_min_conflicts_history()
            self.zone_solution = history[-1]
            self.log("[G5-MinConflicts] Lời giải Min-Conflicts hoàn chỉnh: %s (qua %d bước sửa mâu thuẫn)" % (self.zone_solution, len(history) - 1))

    def place_survivors(self):
        floors = [(r, c) for r in range(self.rows) for c in range(self.cols)
                  if self.grid[r][c] != "#" and (r, c) not in (self.start, self.exit)]
        random.seed(self.seed + 7)
        self.survivors = random.sample(floors, 3)

    # [G3 - Steepest Ascent + Simple Hill Climbing] optimize rescue order
    def optimize_route(self):
        clear_astar_cache()  # Clear cache at start of level route optimization
        uncollected_indices = [i for i in range(len(self.survivors)) if i not in self.collected]
        if not uncollected_indices:
            self.suggested_order = []
            self.route_cells_sa = self.build_route_cells([])
            self.route_cells_hc = self.route_cells_sa
            res = astar(self.gm, self.player, self.exit)
            self.sa_cost = res.cost if res.path else 0.0
            self.hc_cost = self.sa_cost
            return
            
        items = [self.survivors[i] for i in uncollected_indices]
        order0 = list(range(len(items)))
        
        # 1. Tối ưu hóa bằng Simple Hill Climbing cho tính năng di chuyển tự động (Auto-Step)
        hc = simple_hill_climbing(self.gm, self.player, items, self.exit, order0)
        order_hc = [uncollected_indices[idx] for idx in hc["best_order"]]
        self.route_cells_hc = self.build_route_cells(order_hc)
        self.hc_cost = hc["best_cost"]
        
        # 2. Tối ưu hóa bằng Steepest-Ascent Hill Climbing cho tính năng chỉ đường bản đồ (Toggle GPS)
        sa = steepest_ascent_hill_climbing(self.gm, self.player, items, self.exit, order0)
        order_sa = [uncollected_indices[idx] for idx in sa["best_order"]]
        self.route_cells_sa = self.build_route_cells(order_sa)
        self.sa_cost = sa["best_cost"]

    def build_route_cells(self, order):
        pts = [self.player] + [self.survivors[i] for i in order] + [self.exit]
        cells = []
        for i in range(len(pts) - 1):
            res = astar(self.gm, pts[i], pts[i + 1])
            if not res.path:
                return []
            seg = res.path if i == 0 else res.path[1:]
            cells.extend(seg)
        return cells



    def all_floors(self):
        return {(r, c) for r in range(self.rows) for c in range(self.cols) if self.grid[r][c] != "#"}

    def spawn_guards(self):
        random.seed(self.seed + 11)
        floors = [(r, c) for r in range(self.rows) for c in range(self.cols)
                  if self.grid[r][c] != "#" and manhattan((r, c), self.start) > self.rows // 2]
        random.shuffle(floors)
        if len(floors) < 3:
            floors = list(self.all_floors())
            random.shuffle(floors)
        self.guards = [
            {"pos": floors[0], "kind": "astar", "color": T.DANGER},
            {"pos": floors[1], "kind": "greedy", "color": "#ff9f43"},
            {"pos": floors[2], "kind": "stalker", "color": "#9b59b6"},
        ]
        self.stalker_pos = floors[2]
        self.stalker_tracker = StalkerBeliefTracker()
        self.stalker_belief = initialize_stalker_belief(self.gm, exclude_positions={self.stalker_pos})

    # [G6 - Minimax + Alpha-Beta] verify both engines at load
    def benchmark_adversarial(self):
        probe = list("XOX      ")
        _, _, mm = best_move_minimax(TicTacToe(probe))
        _, _, ab = best_move_alpha_beta(TicTacToe(probe))
        self.log("[G6-Minimax] Engine sẵn sàng: duyệt %d nút." % mm["nodes"])
        self.log("[G6-AlphaBeta] Engine sẵn sàng: duyệt %d nút, cắt tỉa %d (hiệu quả hơn)."
                 % (ab["nodes"], ab["prunes"]))

    # ---- per-turn game loop ----
    def move_player(self, dr, dc):
        if self.game_over:
            return
            
        current_cell = self.grid[self.player[0]][self.player[1]]
        nxt = (self.player[0] + dr, self.player[1] + dc)
        
        # 1. Cơ chế trượt chân 50% trên ô Băng I
        if current_cell == "I" and random.random() < 0.50:
            nbs = self.gm.neighbors(self.player)
            if nbs:
                nxt = random.choice(nbs)
                dr = nxt[0] - self.player[0]
                dc = nxt[1] - self.player[1]
                self.log("[Game] Trơn trượt! Robot bị trượt chân trên ô Băng I sang ô %s." % str(nxt))
                
        if not self.gm.passable(nxt):
            return
            
        # 2. Cập nhật vị trí thực tế của Robot
        self.player = nxt
        self.turn += 1
            
        for i, s in enumerate(self.survivors):
            if s == self.player and i not in self.collected:
                self.collected.add(i)
                self.log("[Game] Đã cứu nạn nhân %d (lượt %d)." % (i + 1, self.turn))
        
        self.optimize_route()
        self.process_turn()
        if not self.game_over and self.player == self.exit:
            if len(self.collected) == len(self.survivors):
                self.won = True
                self.game_over = True
                self.log("[Game] THẮNG! Đã cứu hết nạn nhân và tới lối ra.")
            else:
                self.message = "Can cuu du %d nan nhan truoc khi thoat." % len(self.survivors)
        self.emit_status()
        self.update()


    def auto_step_gps(self):
        if self.game_over or self.won:
            return
        if self.hint_uses <= 0:
            self.log("[Game] Đã hết lượt trợ giúp tự động!")
            return
        if not self.route_cells_hc or len(self.route_cells_hc) < 2:
            self.log("[Game] Không có lộ trình khả dụng để đi tự động.")
            return
            
        nxt = self.route_cells_hc[1]
        dr = nxt[0] - self.player[0]
        dc = nxt[1] - self.player[1]
        
        self.hint_uses -= 1
        self.log("[G3-GPS] Sử dụng quyền trợ giúp! Tự động đi tới ô %s (còn %d lượt)." % (str(nxt), self.hint_uses))
        self.move_player(dr, dc)


    def update_guard_paths(self):
        self.guard_paths = []
        for guard in self.guards:
            if guard["kind"] == "astar":
                res = astar(self.gm, guard["pos"], self.player)
            else:
                res = greedy_best_first_search(self.gm, guard["pos"], self.player)
            if res.path:
                self.guard_paths.append((guard["kind"], res.path))

    def process_turn(self):
        if self.game_over:
            return
            
        # [CSP Mechanic] 
        player_zone = "Z%d" % self.zone_of(self.player)
        player_color = self.zone_solution.get(player_zone)
        
        # Red Zone: normal speed (moves every turn)
        # Blue Zone: slow speed (moves only once every 2 player turns)
        should_guards_move = True
        if player_color == "Blue" and self.turn % 2 != 0:
            should_guards_move = False
            self.log("[CSP-System] Bạn đang ở Vùng Lam (Blue) -> Bảo vệ bị gây nhiễu, không thể di chuyển!")
            
        if should_guards_move:
            # [G2 - A* and Greedy] guards chase the player each turn
            for guard in self.guards:
                if guard["kind"] == "astar":
                    res = astar(self.gm, guard["pos"], self.player)
                    if res.path and len(res.path) > 1:
                        guard["pos"] = res.path[1]
                elif guard["kind"] == "greedy":
                    res = greedy_best_first_search(self.gm, guard["pos"], self.player)
                    if res.path and len(res.path) > 1:
                        guard["pos"] = res.path[1]
                elif guard["kind"] == "stalker":
                    dist = manhattan(guard["pos"], self.player)
                    if dist <= 3:
                        res = astar(self.gm, guard["pos"], self.player)
                    else:
                        if not hasattr(self, "stalker_target") or self.stalker_target not in self.stalker_belief or guard["pos"] == self.stalker_target:
                            if self.stalker_belief:
                                self.stalker_target = random.choice(list(self.stalker_belief))
                            else:
                                self.stalker_target = self.player
                        res = astar(self.gm, guard["pos"], self.stalker_target)
                        
                    if res.path and len(res.path) > 1:
                        guard["pos"] = res.path[1]
                        self.stalker_pos = guard["pos"]
                        
            # Cập nhật Belief State (Predict + Observe)
            self.stalker_belief, reading, m = self.stalker_tracker.update(
                self.stalker_belief, self.stalker_pos, self.player, self.gm
            )
            
            if reading == "smelled":
                self.log("[G4-Belief] CẢNH BÁO: Stalker ngửi thấy mùi của bạn! Vùng nghi vấn co cụm lại gần hắn.")
                    
        # Update full path trajectories of the guards to visualize them
        self.update_guard_paths()

        # capture -> [G6] adversarial duel
        # Green Zone: Safe zone! Player cannot be caught in Green Zone.
        if player_color == "Green":
            # Check if any guard is on the player's cell just to print log
            any_guard_here = any(g["pos"] == self.player for g in self.guards)
            if any_guard_here:
                self.log("[CSP-System] Bạn đang ở Vùng Lục (Green) - Vùng An Toàn! Miễn nhiễm bị bảo vệ bắt.")
        else:
            # First, check standard guards
            caught = False
            for guard in self.guards:
                if guard["pos"] == self.player:
                    self.start_duel(guard)
                    caught = True
                    break


    def start_duel(self, guard):
        engine = "minimax" if guard["kind"] == "greedy" else "alphabeta"
        self.log("[G6-%s] Bị bắt bởi Bảo vệ %s! Vào màn đấu trí."
                 % ("Minimax" if engine == "minimax" else "AlphaBeta", "G" if guard["kind"] == "greedy" else "A"))
        dlg = DuelDialog(engine, self)
        dlg.exec_()
        if dlg.player_won or dlg.draw:
            self.log("[Game] Thắng hoặc Hòa đấu trí -> Bạn đã HẠ GỤC bảo vệ vĩnh viễn!")
            if guard in self.guards:
                self.guards.remove(guard)
            if guard.get("kind") == "stalker":
                self.stalker_belief.clear()
            self.update_guard_paths()
        else:
            self.lives -= 1
            if self.lives > 0:
                self.log("[Game] Đấu trí thất bại! Bạn mất 1 mạng (còn lại: %d mạng)." % self.lives)
                self.solve_zone_csp(use_backtracking=True)
                self.respawn_guard(guard)
                self.update_guard_paths()
            else:
                self.game_over = True
                self.log("[Game] Thua đấu trí và đã Hết Mạng Sống! Game Over.")
        self.emit_status()
        self.setFocus()


    def respawn_guard(self, guard):
        cells = [p for p in self.all_floors() if manhattan(p, self.player) > self.rows // 2]
        random.seed(self.seed + self.turn + 99)
        guard["pos"] = random.choice(cells) if cells else guard["pos"]
        if guard.get("kind") == "stalker":
            self.stalker_pos = guard["pos"]
            self.stalker_tracker = StalkerBeliefTracker()
            self.stalker_belief = initialize_stalker_belief(self.gm, exclude_positions={self.stalker_pos})

    def print_and_or_plan(self):
        if self.game_over:
            return
            
        uncollected = [s for i, s in enumerate(self.survivors) if i not in self.collected]
        if uncollected:
            target_goal = min(uncollected, key=lambda t: manhattan(self.player, t))
            target_name = "Nạn nhân 🤕 %d" % (self.survivors.index(target_goal) + 1)
        else:
            target_goal = self.exit
            target_name = "Lối ra 🚪"
            
        self.log("[G4-AND-OR] Lập kế hoạch vượt địa hình trơn trượt đến %s %s..." % (target_name, str(target_goal)))
        t0 = time.perf_counter()
        plan = and_or_graph_search(self.gm, self.player, target_goal)
        dt = (time.perf_counter() - t0) * 1000.0
        
        if plan is None:
            self.log("[G4-AND-OR] Thất bại! Cây tìm kiếm quá lớn hoặc không có lộ trình an toàn.")
            dlg = ContingencyPlanDialog(None, target_goal, dt, self)
            dlg.exec_()
            return
            
        self.log("[G4-AND-OR] Kế hoạch vượt băng thành công! T/g: %.2fms. Sơ đồ:" % dt)
        
        def log_plan(node, indent=""):
            if not node:
                self.log(indent + "└─ ĐẾN ĐÍCH AN TOÀN")
                return
            if isinstance(node, dict) and node.get("LOOP"):
                self.log(indent + "└─ 🔄 Trượt về ô cũ trong lộ trình")
                return
            for act, outcomes in node.items():
                self.log(indent + "└─ Robot chọn đi: <b>%s</b>" % act)
                for out, sub_plan in outcomes.items():
                    self.log(indent + "    ├─ NẾU dạt tới ô %s ->" % str(out))
                    log_plan(sub_plan, indent + "    │   ")
                    
        log_plan(plan)
        
        dlg = ContingencyPlanDialog(plan, target_goal, dt, self)
        dlg.exec_()

    def emit_status(self):
        gd = min((manhattan(g["pos"], self.player) for g in self.guards), default=0)
        self.statusChanged.emit({
            "turn": self.turn,
            "collected": len(self.collected),
            "total": len(self.survivors),
            "guard_dist": gd,
            "dist_exit": self.dist_field.get(self.player, -1),
            "game_over": self.game_over,
            "won": self.won,
            "message": self.message,
            "hint_uses": self.hint_uses,
            "show_gps_guide": self.show_gps_guide,
            "sa_cost": self.sa_cost,
            "hc_cost": self.hc_cost,
            "lives": self.lives,
            "is_blind": bool(self.belief_state),
        })

    # ---- input ----
    def keyPressEvent(self, e):
        k = e.key()
        if hasattr(self, "anim_state") and self.anim_state != "IDLE":
            if k == Qt.Key_R:
                self.new_game()
            return
            
        if k in (Qt.Key_Up, Qt.Key_W):
            self.move_player(-1, 0)
        elif k in (Qt.Key_Down, Qt.Key_S):
            self.move_player(1, 0)
        elif k in (Qt.Key_Left, Qt.Key_A):
            self.move_player(0, -1)
        elif k in (Qt.Key_Right, Qt.Key_D):
            self.move_player(0, 1)
        elif k == Qt.Key_R:
            self.new_game()
        else:
            super().keyPressEvent(e)

    def mouseMoveEvent(self, event):
        c = int(event.x() // self.cell)
        r = int(event.y() // self.cell)
        if 0 <= r < self.rows and 0 <= c < self.cols:
            pos = (r, c)
            tips = []
            
            if pos == self.player:
                tips.append("🤖 <b>Robot (Tác nhân chính)</b>")
            elif pos == self.exit:
                tips.append("🚪 <b>Lối ra an toàn</b> (Dùng BFS tìm đường)")
            
            for i, s in enumerate(self.survivors):
                if s == pos and i not in self.collected:
                    tips.append("🤕 <b>Nạn nhân %d</b> (Cần di chuyển tới để cứu hộ)" % (i + 1))
                    
            for g in self.guards:
                if g["pos"] == pos:
                    if g["kind"] == "astar":
                        tips.append("👮‍♂️ <b>Bảo vệ A*</b>: Đuổi bắt dùng A* Search (Tính chi phí bùn = 3)")
                    elif g["kind"] == "greedy":
                        tips.append("👮‍♂️ <b>Bảo vệ Greedy</b>: Đuổi bắt dùng Greedy Best-First Search")
                    elif g["kind"] == "stalker":
                        tips.append("👻 <b>Stalker (AI Mù)</b>: Đi săn dựa trên thính giác bán kính 3 ô")
                        
            ch = self.grid[r][c]
            if ch == "M":
                tips.append("🟫 <b>Vũng Bùn Lầy</b>: Chi phí di chuyển tốn 3 bước (Bảo vệ A* né ô này)")
            elif ch == "I":
                tips.append("❄️ <b>Băng Trơn Trượt</b>: 50% xác suất trượt chân ngẫu nhiên sang ô lân cận")
            elif ch == "#":
                tips.append("🧱 <b>Tường Chắn</b>: Không thể đi qua")
            else:
                if not tips:
                    tips.append("⬜ <b>Ô Đường Đi Thường</b>: Chi phí di chuyển 1 bước")
                    
            QtWidgets.QToolTip.showText(event.globalPos(), "<br>".join(tips), self)
        else:
            QtWidgets.QToolTip.hideText()

    # ---- rendering ----
    def _token(self, qp, pos, color, text, circle=False, emoji=None, glow_color=None):
        cs = self.cell
        x, y = pos[1] * cs, pos[0] * cs
        
        if glow_color:
            qp.setPen(QtGui.QPen(QtGui.QColor(glow_color), 2))
        else:
            qp.setPen(Qt.NoPen)
            
        qp.setBrush(QtGui.QColor(color))
        if circle:
            qp.drawEllipse(int(x + 2), int(y + 2), int(cs - 5), int(cs - 5))
        else:
            qp.drawRoundedRect(int(x + 2), int(y + 2), int(cs - 5), int(cs - 5), 6, 6)
            
        if emoji:
            font = QtGui.QFont("Segoe UI Emoji", int(cs * 0.46))
            qp.setFont(font)
            qp.setPen(QtGui.QColor("#ffffff"))
            qp.drawText(QRectF(x, y, cs, cs), Qt.AlignCenter, emoji)
        else:
            font = QtGui.QFont("Segoe UI", int(cs * 0.42))
            font.setBold(True)
            qp.setFont(font)
            qp.setPen(QtGui.QColor("#0b1020"))
            qp.drawText(QRectF(x, y, cs, cs), Qt.AlignCenter, text)

    def paintEvent(self, event):
        qp = QtGui.QPainter(self)
        cs = self.cell
        
        for r in range(self.rows):
            for c in range(self.cols):
                ch = self.grid[r][c]
                x, y = c * cs, r * cs
                if ch == "#":
                    if hasattr(self, "wall_pixmap") and not self.wall_pixmap.isNull():
                        qp.drawPixmap(int(x), int(y), self.wall_pixmap)
                        qp.setPen(QtGui.QPen(QtGui.QColor("#232a3d"), 1))
                        qp.drawRect(int(x), int(y), int(cs), int(cs))
                        continue
                    else:
                        qp.fillRect(int(x), int(y), int(cs), int(cs), QtGui.QColor("#1a1a1a"))
                        qp.setPen(QtGui.QPen(QtGui.QColor("#3a4563"), 1))
                        qp.drawLine(int(x), int(y), int(x + cs - 1), int(y))
                        qp.drawLine(int(x), int(y), int(x), int(y + cs - 1))
                        qp.setPen(QtGui.QPen(QtGui.QColor("#0a0d14"), 1))
                        qp.drawLine(int(x + cs - 1), int(y), int(x + cs - 1), int(y + cs - 1))
                        qp.drawLine(int(x), int(y + cs - 1), int(x + cs - 1), int(y + cs - 1))
                        continue
                elif ch == "M":
                    qp.fillRect(int(x), int(y), int(cs), int(cs), QtGui.QColor("#5D4037"))
                    qp.setPen(QtGui.QPen(QtGui.QColor("#8D6E63"), 1, Qt.DashLine))
                    qp.drawRect(int(x), int(y), int(cs - 1), int(cs - 1))
                    font_emoji = QtGui.QFont("Segoe UI Emoji", int(cs * 0.35))
                    qp.setFont(font_emoji)
                    qp.setPen(QtGui.QColor("#3E2723"))
                    qp.drawText(QRectF(x, y, cs, cs), Qt.AlignCenter, "🐾")
                    continue
                elif ch == "I":
                    grad = QtGui.QLinearGradient(x, y, x + cs, y + cs)
                    grad.setColorAt(0, QtGui.QColor("#E0F7FA"))
                    grad.setColorAt(1, QtGui.QColor("#81D4FA"))
                    qp.fillRect(int(x), int(y), int(cs), int(cs), grad)
                    qp.setPen(QtGui.QPen(QtGui.QColor("#4FC3F7"), 1))
                    qp.drawRect(int(x), int(y), int(cs - 1), int(cs - 1))
                    font_emoji = QtGui.QFont("Segoe UI Emoji", int(cs * 0.35))
                    qp.setFont(font_emoji)
                    qp.setPen(QtGui.QColor("#01579B"))
                    qp.drawText(QRectF(x, y, cs, cs), Qt.AlignCenter, "❄️")
                    continue
                else:
                    col = QtGui.QColor(self.zone_tint((r, c)))
                    qp.fillRect(int(x), int(y), int(cs), int(cs), col)
                    qp.setPen(QtGui.QPen(QtGui.QColor("#232a3d"), 1))
                    qp.drawRect(int(x), int(y), int(cs), int(cs))

        if hasattr(self, "anim_state") and hasattr(self, "latest_carved_pos") and self.latest_carved_pos:
            if self.anim_state in ("CARVING", "ZONES"):
                r, c = self.latest_carved_pos
                x, y = c * cs, r * cs
                indicator = "⚡" if self.anim_state == "CARVING" else "✨"
                color_tint = QtGui.QColor(255, 209, 102, 140) if self.anim_state == "CARVING" else QtGui.QColor(129, 212, 250, 160)
                qp.fillRect(int(x), int(y), int(cs), int(cs), color_tint)
                font_drill = QtGui.QFont("Segoe UI Emoji", int(cs * 0.5))
                qp.setFont(font_drill)
                qp.drawText(QRectF(x, y, cs, cs), Qt.AlignCenter, indicator)

        if not hasattr(self, "anim_state") or self.anim_state in ("IDLE", "ENTITIES"):
            if self.show_gps_guide and self.route_cells_sa:
                # 1. Đường nối Neon Cyan mờ bên dưới
                pen_glow = QtGui.QPen(QtGui.QColor(0, 255, 255, 100), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                qp.setPen(pen_glow)
                qp.setBrush(Qt.NoBrush)
                path = QtGui.QPainterPath()
                r0, c0 = self.route_cells_sa[0]
                path.moveTo(c0 * cs + cs / 2, r0 * cs + cs / 2)
                for (r, c) in self.route_cells_sa[1:]:
                    path.lineTo(c * cs + cs / 2, r * cs + cs / 2)
                qp.drawPath(path)
                
                # 2. Vẽ Bộ Mũi Tên Neon Sci-Fi Cyan (▲ ▼ ◄ ►)
                font_arrow = QtGui.QFont("Segoe UI Symbol", int(cs * 0.44))
                font_arrow.setBold(True)
                qp.setFont(font_arrow)
                qp.setPen(QtGui.QColor("#00FFFF"))
                
                drawn_cells = set()
                for i in range(len(self.route_cells_sa) - 1):
                    r1, c1 = self.route_cells_sa[i]
                    r2, c2 = self.route_cells_sa[i + 1]
                    
                    if (r1, c1) == self.player or (r1, c1) in drawn_cells:
                        continue
                    drawn_cells.add((r1, c1))
                    
                    dr = r2 - r1
                    dc = c2 - c1
                    
                    arrow_char = "►"
                    if dr == -1:
                        arrow_char = "▲"
                    elif dr == 1:
                        arrow_char = "▼"
                    elif dc == -1:
                        arrow_char = "◄"
                    elif dc == 1:
                        arrow_char = "►"
                        
                    x1, y1 = c1 * cs, r1 * cs
                    qp.drawText(QRectF(x1, y1, cs, cs), Qt.AlignCenter, arrow_char)

            self._token(qp, self.exit, "#1a2620", "E", circle=False, emoji="🚪", glow_color="#2ECC71")
            for trap in self.fog_traps:
                self._token(qp, trap, "#5f4b8b", "F")
            for i, s in enumerate(self.survivors):
                if i not in self.collected:
                    self._token(qp, s, "#3d2b1f", str(i + 1), circle=False, emoji="🤕", glow_color="#FFD700")
            for g in self.guards:
                if g["kind"] == "astar":
                    self._token(qp, g["pos"], "#3d1f24", "A", circle=True, emoji="👮‍♂️", glow_color="#FF0000")
                elif g["kind"] == "greedy":
                    self._token(qp, g["pos"], "#3d2e1f", "G", circle=True, emoji="👮‍♂️", glow_color="#FF8C00")
                else:
                    self._token(qp, g["pos"], "#2e1f3d", "S", circle=True, emoji="👻", glow_color="#9B59B6")
                
            self._token(qp, self.player, "#1b3a4b", "R", circle=False, emoji="🤖", glow_color="#00FFFF")

            if hasattr(self, "selected_tree_cell") and self.selected_tree_cell:
                r, c = self.selected_tree_cell
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    x, y = c * cs, r * cs
                    qp.fillRect(int(x), int(y), int(cs), int(cs), QtGui.QColor(255, 0, 255, 90))
                    pen_hlt = QtGui.QPen(QtGui.QColor("#FF00FF"), 3, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
                    qp.setPen(pen_hlt)
                    qp.setBrush(Qt.NoBrush)
                    qp.drawRect(int(x + 1), int(y + 1), int(cs - 2), int(cs - 2))
                    font_tgt = QtGui.QFont("Segoe UI Symbol", int(cs * 0.45))
                    font_tgt.setBold(True)
                    qp.setFont(font_tgt)
                    qp.setPen(QtGui.QColor("#FFFFFF"))
                    qp.drawText(QRectF(x, y, cs, cs), Qt.AlignCenter, "🎯")

        if self.game_over:
            qp.setBrush(QtGui.QColor(15, 17, 24, 205))
            qp.setPen(Qt.NoPen)
            qp.drawRect(0, 0, self.width(), self.height())
            qp.setPen(QtGui.QColor(T.OK if self.won else T.DANGER))
            big = QtGui.QFont("Segoe UI", 26)
            big.setBold(True)
            qp.setFont(big)
            msg = "THANG!" if self.won else "GAME OVER"
            qp.drawText(self.rect(), Qt.AlignCenter, msg + "  (nhan R de choi lai)")
        qp.end()


# ============================================================
#  DUEL DIALOG  (Group 5 applied during gameplay)
# ============================================================

class DuelDialog(QtWidgets.QDialog):
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.game = TicTacToe()
        self.player_won = False
        self.draw = False
        
        self.setWindowTitle("Đấu Trí Bảo Vệ")
        self.setFixedSize(310, 430)
        self.setStyleSheet("background: #0f1118; color: #e8ebf2;")
        
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)
        
        # Header warning
        header = QtWidgets.QLabel("⚠️ PHÁT HIỆN BẢO VỆ!")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #ff6b6b; font-size: 15px; font-weight: bold;")
        lay.addWidget(header)
        
        # Subtitle info
        info = QtWidgets.QLabel(
            "Bạn là X (Xanh). Thắng hoặc Hòa để trốn thoát!\n"
            "Đối thủ AI sử dụng: %s" % ("Minimax" if engine == "minimax" else "Alpha-Beta")
        )
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #8b93ad; font-size: 11px; line-height: 14px;")
        lay.addWidget(info)
        
        # Grid board
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(8)
        self.buttons = []
        for i in range(9):
            b = QtWidgets.QPushButton("")
            b.setFixedSize(80, 80)
            b.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
            b.clicked.connect(lambda _=False, idx=i: self.human(idx))
            grid.addWidget(b, i // 3, i % 3)
            self.buttons.append(b)
        lay.addLayout(grid)
        
        # Status footer
        self.status = QtWidgets.QLabel("")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setFixedHeight(34)
        lay.addWidget(self.status)
        
        self.set_status_style("play_user")
        self.render()

    def set_status_style(self, state, text=""):
        if state == "play_user":
            self.status.setText("👉 LƯỢT CỦA BẠN (X)")
            self.status.setStyleSheet("""
                background: #161a26;
                color: #5b8cff;
                border: 1px solid #2f3d6b;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            """)
        elif state == "play_ai":
            self.status.setText("🤖 BẢO VỆ ĐANG TÍNH (O)...")
            self.status.setStyleSheet("""
                background: #161a26;
                color: #ff9f43;
                border: 1px solid #5d4037;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            """)
        elif state == "win":
            self.status.setText("🎉 BẠN THẮNG! ĐÃ TRỐN THOÁT")
            self.status.setStyleSheet("""
                background: #19241f;
                color: #22d3a6;
                border: 1px solid #22d3a6;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            """)
        elif state == "lose":
            self.status.setText("💀 BẢO VỆ THẮNG! BỊ BẮT")
            self.status.setStyleSheet("""
                background: #241a22;
                color: #ff6b6b;
                border: 1px solid #ff6b6b;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            """)
        elif state == "draw":
            self.status.setText("🤝 HÒA! BẠN ĐÃ THOÁT NẠN")
            self.status.setStyleSheet("""
                background: #2b261a;
                color: #ffd166;
                border: 1px solid #ffd166;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            """)

    def render(self):
        for i, ch in enumerate(self.game.board):
            b = self.buttons[i]
            if ch == "X":
                b.setText("X")
                b.setStyleSheet("""
                    background: #1b2030;
                    color: #22d3a6;
                    border: 2px solid #22d3a6;
                    font-size: 32px;
                    font-weight: bold;
                    border-radius: 12px;
                """)
            elif ch == "O":
                b.setText("O")
                b.setStyleSheet("""
                    background: #1b2030;
                    color: #ff6b6b;
                    border: 2px solid #ff6b6b;
                    font-size: 32px;
                    font-weight: bold;
                    border-radius: 12px;
                """)
            else:
                b.setText("")
                b.setStyleSheet("""
                    QPushButton {
                        background: #1b2030;
                        color: #e8ebf2;
                        border: 2px solid #2c3350;
                        border-radius: 12px;
                    }
                    QPushButton:hover {
                        background: #232a3d;
                        border: 2px solid #5b8cff;
                    }
                """)

    def human(self, idx):
        if self.game.board[idx] != EMPTY or self.game.terminal():
            return
        self.game.board[idx] = "X"
        self.render()
        if self.check():
            return
            
        self.set_status_style("play_ai")
        # Cho phép UI cập nhật hiển thị trạng thái đang tính của AI
        QtWidgets.QApplication.processEvents()
        
        # Thêm một khoảng trễ nhỏ 200ms tạo cảm giác AI đang suy nghĩ thực tế
        time.sleep(0.2)
        
        if self.engine == "minimax":
            mv, _, _ = best_move_minimax(self.game)
        else:
            mv, _, _ = best_move_alpha_beta(self.game)
            
        if mv >= 0:
            self.game.board[mv] = "O"
            
        self.render()
        if not self.check():
            self.set_status_style("play_user")

    def check(self):
        if self.game.terminal():
            w = self.game.winner()
            if w == "X":
                self.player_won = True
                self.set_status_style("win")
            elif w == "O":
                self.set_status_style("lose")
            else:
                self.draw = True
                self.set_status_style("draw")
            QTimer.singleShot(1000, self.accept)
            return True
        return False


# ============================================================
#  CONTINGENCY PLAN DIALOG  (Group 4 AND-OR Visualization)
# ============================================================

class ContingencyPlanDialog(QtWidgets.QDialog):
    def __init__(self, plan: Optional[Dict], target: Position, runtime_ms: float, parent=None):
        super().__init__(parent)
        self.plan = plan
        self.target = target
        self.runtime_ms = runtime_ms
        
        self.setWindowTitle("Cây Kế Hoạch Dự Phòng (Contingency Plan)")
        self.resize(720, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f1118;
                color: #e8ebf2;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)
        
        header = QtWidgets.QLabel("🌳 CÂY KẾ HOẠCH DỰ PHÒNG (CONTINGENCY PLAN)")
        header.setStyleSheet("color: #22d3a6; font-size: 16px; font-weight: bold; letter-spacing: 0.5px;")
        lay.addWidget(header)
        
        sub = QtWidgets.QLabel("Mô phỏng thuật toán AND-OR Graph Search xử lý rủi ro trượt chân trên các ô Băng (Ice).")
        sub.setStyleSheet("color: #8b93ad; font-size: 12px;")
        lay.addWidget(sub)
        
        info_panel = QtWidgets.QFrame()
        info_panel.setStyleSheet("""
            QFrame {
                background: #161a26;
                border: 1px solid #232a3d;
                border-radius: 8px;
            }
        """)
        info_lay = QtWidgets.QHBoxLayout(info_panel)
        info_lay.setContentsMargins(16, 10, 16, 10)
        
        t_box = QtWidgets.QLabel("🎯 Mục tiêu: <b style='color:#ffd166;'>%s</b>" % str(target))
        t_box.setStyleSheet("color: #e8ebf2; font-size: 12px;")
        info_lay.addWidget(t_box)
        
        info_lay.addStretch()
        
        time_box = QtWidgets.QLabel("⚡ Thời gian tính: <b style='color:#5b8cff;'>%.2f ms</b>" % runtime_ms)
        time_box.setStyleSheet("color: #e8ebf2; font-size: 12px;")
        info_lay.addWidget(time_box)
        
        info_lay.addStretch()
        
        status_text = "<span style='color:#22d3a6;'>THÀNH CÔNG</span>" if plan is not None else "<span style='color:#ff6b6b;'>THẤT BẠI</span>"
        status_box = QtWidgets.QLabel("Trạng thái: <b>%s</b>" % status_text)
        status_box.setStyleSheet("color: #e8ebf2; font-size: 12px;")
        info_lay.addWidget(status_box)
        
        lay.addWidget(info_panel)
        
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(24)
        self.tree.setAutoScroll(False)
        self.tree.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.tree.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #161a26;
                border: 1px solid #232a3d;
                border-radius: 8px;
                padding: 10px;
                color: #e8ebf2;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 6px 4px;
                border-bottom: 1px solid #1b2030;
                border-radius: 4px;
            }
            QTreeWidget::item:hover {
                background-color: #232a3d;
            }
            QTreeWidget::item:selected {
                background-color: #2f3d6b;
                color: #ffffff;
            }
            QScrollBar:horizontal {
                height: 10px;
                background: #161a26;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background: #3d4a6b;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #5b8cff;
            }
        """)
        self.tree.currentItemChanged.connect(self.on_item_selected)
        self.tree.itemClicked.connect(self.on_item_selected)
        lay.addWidget(self.tree)
        
        start_pos = None
        if hasattr(parent, "board") and hasattr(parent.board, "player"):
            start_pos = parent.board.player
        elif hasattr(parent, "player"):
            start_pos = parent.player

        if plan is not None:
            self._build_tree(plan, self.tree.invisibleRootItem(), start_pos)
            self.tree.expandAll()
        else:
            fail_item = QtWidgets.QTreeWidgetItem(self.tree)
            fail_item.setText(0, "❌ THẤT BẠI: Không tìm thấy chiến thuật dự phòng đảm bảo 100% an toàn.")
            fail_item.setForeground(0, QtGui.QColor("#ff6b6b"))
            font = fail_item.font(0)
            font.setBold(True)
            fail_item.setFont(0, font)
            
            summary_item = QtWidgets.QTreeWidgetItem(fail_item)
            summary_item.setText(0, "📌 Tóm tắt phân tích Lý thuyết AI (AND-OR Graph Search):")
            summary_item.setForeground(0, QtGui.QColor("#5b8cff"))
            
            reason1 = QtWidgets.QTreeWidgetItem(summary_item)
            reason1.setText(0, "1️⃣ Điểm xuất phát: %s  ➜  Mục tiêu: %s" % (str(start_pos), str(target)))
            reason1.setForeground(0, QtGui.QColor("#e8ebf2"))
            if start_pos:
                reason1.setData(0, Qt.UserRole, start_pos)
                
            reason2 = QtWidgets.QTreeWidgetItem(summary_item)
            reason2.setText(0, "2️⃣ Rủi ro địa hình: Tồn tại các ô Băng ❄️ gây trượt chân ngẫu nhiên (Nút AND môi trường).")
            reason2.setForeground(0, QtGui.QColor("#ffd166"))
            
            reason3 = QtWidgets.QTreeWidgetItem(summary_item)
            reason3.setText(0, "3️⃣ Nguyên nhân thất bại: Mọi chiến thuật đều có ít nhất 1 nhánh trượt chân văng vào ngõ cụt/vòng lặp không thể tới mục tiêu.")
            reason3.setForeground(0, QtGui.QColor("#ff9f43"))

            board_obj = None
            if hasattr(self.parent(), "board"):
                board_obj = self.parent().board
            elif hasattr(self.parent(), "gm"):
                board_obj = self.parent()

            if start_pos and board_obj and hasattr(board_obj, "gm"):
                gm = board_obj.gm
                dirs = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}
                
                detail_root = QtWidgets.QTreeWidgetItem(fail_item)
                detail_root.setText(0, "🔍 Phân tích chi tiết 4 hướng di chuyển từ vị trí %s:" % str(start_pos))
                detail_root.setForeground(0, QtGui.QColor("#22d3a6"))
                
                for act, (dr, dc) in dirs.items():
                    nxt = (start_pos[0] + dr, start_pos[1] + dc)
                    act_node = QtWidgets.QTreeWidgetItem(detail_root)
                    act_node.setData(0, Qt.UserRole, start_pos)
                    
                    if not gm.passable(nxt):
                        act_node.setText(0, "🚫 Hướng [%s] -> Ô %s: BỊ CHẶN BỞI TƯỜNG CHẮN #" % (act, str(nxt)))
                        act_node.setForeground(0, QtGui.QColor("#ff6b6b"))
                    else:
                        cell_type = gm.cell(nxt)
                        tag = " [Ô Băng ❄️]" if cell_type == "I" else (" [Ô Bùn 🐾]" if cell_type == "M" else " [Đường thường ⬜]")
                        act_node.setText(0, "🤖 Hướng [%s] -> Ô %s%s" % (act, str(nxt), tag))
                        act_node.setForeground(0, QtGui.QColor("#5b8cff"))
                        
                        if gm.cell(start_pos) == "I":
                            for nb in gm.neighbors(start_pos):
                                slip_node = QtWidgets.QTreeWidgetItem(act_node)
                                slip_node.setData(0, Qt.UserRole, nb)
                                slip_tag = " [Ô Băng ❄️]" if gm.cell(nb) == "I" else " [Đường ⬜]"
                                slip_node.setText(0, "⚡ Nhánh trượt (Nút AND) sang %s%s: Không thể tạo đường an toàn 100%%" % (str(nb), slip_tag))
                                slip_node.setForeground(0, QtGui.QColor("#ffd166"))
                        else:
                            slip_node = QtWidgets.QTreeWidgetItem(act_node)
                            slip_node.setData(0, Qt.UserRole, nxt)
                            slip_node.setText(0, "⚡ Nhánh di chuyển sang %s: Không thể tìm thấy cây dự phòng hoàn chỉnh tới %s" % (str(nxt), str(target)))
                            slip_node.setForeground(0, QtGui.QColor("#ffd166"))
            
            self.tree.expandAll()

        footer = QtWidgets.QHBoxLayout()
        
        btn_expand = QtWidgets.QPushButton("📖 Mở rộng tất cả")
        btn_expand.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
        btn_expand.setStyleSheet(self._btn_secondary_style())
        btn_expand.clicked.connect(self.tree.expandAll)
        footer.addWidget(btn_expand)
        
        btn_collapse = QtWidgets.QPushButton("📘 Thu gọn")
        btn_collapse.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
        btn_collapse.setStyleSheet(self._btn_secondary_style())
        btn_collapse.clicked.connect(self.tree.collapseAll)
        footer.addWidget(btn_collapse)
        
        footer.addStretch()
        
        btn_close = QtWidgets.QPushButton("Đóng Màn Hình")
        btn_close.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
        btn_close.setStyleSheet("""
            QPushButton {
                background: #5b8cff;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #4a7be0;
            }
        """)
        btn_close.clicked.connect(self.accept)
        footer.addWidget(btn_close)
        
        lay.addLayout(footer)

    def on_item_selected(self, item, col=0):
        if not item:
            return
        h_val = self.tree.horizontalScrollBar().value()
        v_val = self.tree.verticalScrollBar().value()
        
        pos = item.data(0, Qt.UserRole)
        board = None
        if hasattr(self.parent(), "board"):
            board = self.parent().board
        elif hasattr(self.parent(), "gm"):
            board = self.parent()
            
        if board:
            board.selected_tree_cell = pos
            board.update()
            
        self.tree.horizontalScrollBar().setValue(h_val)
        self.tree.verticalScrollBar().setValue(v_val)

    def closeEvent(self, event):
        self._clear_board_highlight()
        super().closeEvent(event)
        
    def accept(self):
        self._clear_board_highlight()
        super().accept()
        
    def reject(self):
        self._clear_board_highlight()
        super().reject()

    def _clear_board_highlight(self):
        board = None
        if hasattr(self.parent(), "board"):
            board = self.parent().board
        elif hasattr(self.parent(), "gm"):
            board = self.parent()
        if board:
            board.selected_tree_cell = None
            board.update()

    def _btn_secondary_style(self):
        return """
            QPushButton {
                background: #232a3d;
                color: #e8ebf2;
                border: 1px solid #2c3350;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #2f3d6b;
                border-color: #5b8cff;
            }
        """

    def _build_tree(self, node: Optional[Dict], parent_item, current_pos=None):
        if not node:
            goal_item = QtWidgets.QTreeWidgetItem(parent_item)
            goal_item.setText(0, "✅ ĐẾN ĐÍCH AN TOÀN!")
            goal_item.setForeground(0, QtGui.QColor("#22d3a6"))
            font = goal_item.font(0)
            font.setBold(True)
            goal_item.setFont(0, font)
            goal_item.setData(0, Qt.UserRole, self.target)
            return

        if isinstance(node, dict) and node.get("LOOP"):
            loop_item = QtWidgets.QTreeWidgetItem(parent_item)
            loop_item.setText(0, "🔄 Trượt về ô cũ trong lộ trình (Thử lại nước đi)")
            loop_item.setForeground(0, QtGui.QColor("#ff9f43"))
            loop_item.setData(0, Qt.UserRole, current_pos)
            return

        for act, outcomes in node.items():
            act_item = QtWidgets.QTreeWidgetItem(parent_item)
            act_item.setText(0, "🤖 Robot chọn đi: [%s]  (Nút OR)" % act)
            act_item.setForeground(0, QtGui.QColor("#5b8cff"))
            font = act_item.font(0)
            font.setBold(True)
            act_item.setFont(0, font)
            act_item.setData(0, Qt.UserRole, current_pos)
            
            for out, sub_plan in outcomes.items():
                out_item = QtWidgets.QTreeWidgetItem(act_item)
                
                tag = ""
                board = None
                if hasattr(self.parent(), "board"):
                    board = self.parent().board
                elif hasattr(self.parent(), "gm"):
                    board = self.parent()
                    
                if board and hasattr(board, "gm"):
                    cell_type = board.gm.cell(out)
                    if cell_type == "I":
                        tag = " [Ô Băng ❄️]"
                    elif cell_type == "M":
                        tag = " [Ô Bùn 🐾]"
                    elif cell_type == ".":
                        tag = " [Đường thường ⬜]"
                        
                out_item.setText(0, "⚡ Kết quả môi trường (Nút AND): Sang ô %s%s" % (str(out), tag))
                out_item.setForeground(0, QtGui.QColor("#ffd166"))
                out_item.setData(0, Qt.UserRole, out)
                
                self._build_tree(sub_plan, out_item, out)


# ============================================================
#  MAIN WINDOW
# ============================================================

class GameWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Maze Quest - All-in-One")
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        h = QtWidgets.QHBoxLayout(central)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        left = QtWidgets.QVBoxLayout()
        left.setContentsMargins(16, 14, 16, 14)
        title = QtWidgets.QLabel("AI MAZE QUEST")
        title.setObjectName("Brand")
        sub = QtWidgets.QLabel("Mot game - 10 thuat toan AI - Mui ten/WASD de di, R de choi lai")
        sub.setObjectName("Subtitle")
        left.addWidget(title)
        left.addWidget(sub)
        self.board = BoardWidget()
        left.addWidget(self.board, 0, Qt.AlignTop | Qt.AlignLeft)
        left.addStretch(1)
        lw = QtWidgets.QWidget()
        lw.setLayout(left)
        h.addWidget(lw)

        side = QtWidgets.QVBoxLayout()
        side.setContentsMargins(14, 14, 14, 14)
        lbl1 = QtWidgets.QLabel("TRẠNG THÁI & BẢN ĐỒ THU NHỎ")
        lbl1.setObjectName("SectionLabel")
        side.addWidget(lbl1)

        self.minimap = MinimapWidget(self.board)
        side.addWidget(self.minimap, 0, Qt.AlignCenter)

        # Lưới 3 hàng, 2 cột chứa các ô trạng thái chuyên nghiệp
        status_grid = QtWidgets.QGridLayout()
        status_grid.setSpacing(8)

        self.card_turn = self.create_status_card("LƯỢT ĐI", "0", "#5b8cff")
        self.card_lives = self.create_status_card("MẠNG SỐNG", "❤️ ❤️ ❤️", "#ff6b6b")
        self.card_rescue = self.create_status_card("CỨU HỘ", "0/3", "#c792ea")
        self.card_exit = self.create_status_card("LỐI RA (BFS)", "N/A", "#22d3a6")
        self.card_guard = self.create_status_card("BẢO VỆ GẦN", "N/A", "#ff6b6b")

        status_grid.addWidget(self.card_turn, 0, 0)
        status_grid.addWidget(self.card_lives, 0, 1)
        status_grid.addWidget(self.card_rescue, 1, 0)
        status_grid.addWidget(self.card_exit, 1, 1)
        status_grid.addWidget(self.card_guard, 2, 0, 1, 2)
        side.addLayout(status_grid)

        # Nhãn thông báo kết quả Game Over / Hints
        self.status_msg = QtWidgets.QLabel("")
        self.status_msg.setAlignment(Qt.AlignCenter)
        self.status_msg.setStyleSheet("color: #ffd166; font-weight: bold; font-size: 12px; margin-top: 4px; min-height: 20px;")
        side.addWidget(self.status_msg)

        # Panel Tính Năng Hỗ Trợ
        lbl_g3 = QtWidgets.QLabel("TÍNH NĂNG HỖ TRỢ")
        lbl_g3.setObjectName("SectionLabel")
        side.addWidget(lbl_g3)

        g3_frame = QtWidgets.QFrame()
        g3_frame.setStyleSheet("""
            QFrame {
                background: #1b2030;
                border: 1px solid #2c3350;
                border-radius: 8px;
            }
        """)
        g3_layout = QtWidgets.QVBoxLayout(g3_frame)
        g3_layout.setContentsMargins(10, 8, 10, 8)
        g3_layout.setSpacing(8)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(6)

        self.btn_toggle_gps = QtWidgets.QPushButton("Bật Chỉ Đường")
        self.btn_toggle_gps.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
        self.btn_toggle_gps.setStyleSheet("""
            QPushButton {
                background: #232a3d;
                color: #e8ebf2;
                border: 1px solid #2c3350;
                border-radius: 6px;
                padding: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #2f3d6b;
                border: 1px solid #5b8cff;
            }
        """)
        self.btn_toggle_gps.clicked.connect(self.on_toggle_gps)

        self.btn_auto_step = QtWidgets.QPushButton("Đi Tự Động")
        self.btn_auto_step.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
        self.btn_auto_step.setStyleSheet("""
            QPushButton {
                background: #232a3d;
                color: #e8ebf2;
                border: 1px solid #2c3350;
                border-radius: 6px;
                padding: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #2f3d6b;
                border: 1px solid #5b8cff;
            }
        """)
        self.btn_auto_step.clicked.connect(self.on_auto_step)

        btn_layout.addWidget(self.btn_toggle_gps)
        btn_layout.addWidget(self.btn_auto_step)
        g3_layout.addLayout(btn_layout)

        self.lbl_hint_count = QtWidgets.QLabel("Lượt đi tự động còn lại: 3")
        self.lbl_hint_count.setAlignment(Qt.AlignCenter)
        self.lbl_hint_count.setStyleSheet("color: #ffd166; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        g3_layout.addWidget(self.lbl_hint_count)
        side.addWidget(g3_frame)

        # Panel Môi Trường Đặc Biệt
        lbl_g6 = QtWidgets.QLabel("MÔI TRƯỜNG ĐẶC BIỆT")
        lbl_g6.setObjectName("SectionLabel")
        side.addWidget(lbl_g6)

        g6_frame = QtWidgets.QFrame()
        g6_frame.setStyleSheet("""
            QFrame {
                background: #1b2030;
                border: 1px solid #2c3350;
                border-radius: 8px;
            }
        """)
        g6_layout = QtWidgets.QVBoxLayout(g6_frame)
        g6_layout.setContentsMargins(10, 8, 10, 8)
        g6_layout.setSpacing(8)

        self.btn_and_or = QtWidgets.QPushButton("Kế Hoạch Vượt Băng")
        self.btn_and_or.setCursor(QtGui.QCursor(Qt.PointingHandCursor))
        self.btn_and_or.setStyleSheet("""
            QPushButton {
                background: #232a3d;
                color: #e8ebf2;
                border: 1px solid #2c3350;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #2f3d6b;
                border: 1px solid #5b8cff;
            }
        """)
        self.btn_and_or.clicked.connect(self.on_and_or_plan)

        g6_layout.addWidget(self.btn_and_or)
        side.addWidget(g6_frame)

        lbl2 = QtWidgets.QLabel("NHAT KY HE THONG AI")
        lbl2.setObjectName("SectionLabel")
        side.addWidget(lbl2)
        self.log_view = QtWidgets.QTextEdit()
        self.log_view.setReadOnly(True)
        # Use HTML log support
        self.log_view.setAcceptRichText(True)
        side.addWidget(self.log_view, 1)
        
        legend = QtWidgets.QLabel(
            "🤖 Robot - 🚪 Lối ra - 🤕 Nạn nhân\n"
            "👮‍♂️ Bảo vệ A* / Greedy (Đuổi bắt)\n"
            "👻 Stalker (AI Mù đi săn thính giác)\n"
            "Mũi tên: Lộ trình đề xuất (HC/SA)")
        legend.setStyleSheet("color: #8b93ad; font-size: 11px;")
        side.addWidget(legend)
        sw = QtWidgets.QWidget()
        sw.setFixedWidth(360)
        sw.setLayout(side)
        sw.setStyleSheet("background: #161a26;")
        h.addWidget(sw)

        self.board.logMessage.connect(self.log_view.append)
        self.board.statusChanged.connect(self.on_status)
        self.resize(1100, 620)
        self.board.new_game()
        self.board.setFocus()



    def create_status_card(self, title: str, value: str, accent_color: str) -> QtWidgets.QFrame:
        card = QtWidgets.QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #1b2030;
                border: 1px solid #2c3350;
                border-radius: 8px;
            }
        """)
        card.setFixedHeight(60)
        
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)
        
        t_lbl = QtWidgets.QLabel(title)
        t_lbl.setAlignment(Qt.AlignCenter)
        t_lbl.setStyleSheet("color: #8b93ad; font-size: 10px; font-weight: bold; border: none; background: transparent;")
        
        v_lbl = QtWidgets.QLabel(value)
        v_lbl.setAlignment(Qt.AlignCenter)
        v_lbl.setStyleSheet(f"color: {accent_color}; font-size: 16px; font-weight: bold; font-family: Consolas, monospace; border: none; background: transparent;")
        
        layout.addWidget(t_lbl)
        layout.addWidget(v_lbl)
        
        card.title_label = t_lbl
        card.value_label = v_lbl
        card.accent_color = accent_color
        return card

    def on_toggle_gps(self):
        self.board.show_gps_guide = not self.board.show_gps_guide
        self.board.update()
        self.board.emit_status()
        self.board.setFocus()

    def on_auto_step(self):
        self.board.auto_step_gps()
        self.board.setFocus()

    def on_and_or_plan(self):
        self.board.print_and_or_plan()
        self.board.setFocus()

    def on_status(self, s):
        if hasattr(self, "minimap"):
            self.minimap.update()
        # Cập nhật số liệu các ô
        self.card_turn.value_label.setText(str(s["turn"]))
        self.card_rescue.value_label.setText("%d/%d" % (s["collected"], s["total"]))
        
        lives = s.get("lives", 3)
        hearts = "❤️ " * lives + "🖤 " * (3 - lives)
        self.card_lives.value_label.setText(hearts.strip())
        
        dist_exit_str = str(s["dist_exit"]) if s["dist_exit"] != -1 else "N/A"
        self.card_exit.value_label.setText(dist_exit_str)
        
        # Thiết kế viền cảnh báo động và trạng thái cho Bảo vệ
        gd = s["guard_dist"]
        if gd >= 10:
            self.card_guard.value_label.setText("%d (An toàn)" % gd)
            self.card_guard.value_label.setStyleSheet("color: #22d3a6; font-size: 14px; font-weight: bold; font-family: Consolas, monospace; border: none; background: transparent;")
            self.card_guard.setStyleSheet("""
                QFrame {
                    background: #19241f;
                    border: 1px solid #22d3a6;
                    border-radius: 8px;
                }
            """)
        elif 5 <= gd <= 9:
            self.card_guard.value_label.setText("%d (Cảnh báo)" % gd)
            self.card_guard.value_label.setStyleSheet("color: #ffd166; font-size: 14px; font-weight: bold; font-family: Consolas, monospace; border: none; background: transparent;")
            self.card_guard.setStyleSheet("""
                QFrame {
                    background: #2b261a;
                    border: 1px solid #ffd166;
                    border-radius: 8px;
                }
            """)
        else:
            self.card_guard.value_label.setText("%d (NGUY HIỂM!)" % gd)
            self.card_guard.value_label.setStyleSheet("color: #ff6b6b; font-size: 14px; font-weight: bold; font-family: Consolas, monospace; border: none; background: transparent;")
            self.card_guard.setStyleSheet("""
                QFrame {
                    background: #281a20;
                    border: 2px solid #ff6b6b;
                    border-radius: 8px;
                }
            """)

        # Thiết kế viền cảnh báo động cho Lối ra
        if s["dist_exit"] != -1 and s["dist_exit"] <= 3:
            self.card_exit.setStyleSheet("""
                QFrame {
                    background: #1a2620;
                    border: 2px solid #22d3a6;
                    border-radius: 8px;
                }
            """)
        else:
            self.card_exit.setStyleSheet("""
                QFrame {
                    background: #1b2030;
                    border: 1px solid #2c3350;
                    border-radius: 8px;
                }
            """)



        # Cập nhật thông số GPS trợ giúp & trạng thái nút
        self.lbl_hint_count.setText("Lượt đi tự động còn lại: %d" % s["hint_uses"])
        
        # Cập nhật nút trạng thái bật/tắt chỉ đường (Active vs Inactive)
        self.btn_toggle_gps.setText("Tắt Chỉ Đường" if s["show_gps_guide"] else "Bật Chỉ Đường")
        if s["show_gps_guide"]:
            self.btn_toggle_gps.setStyleSheet("""
                QPushButton {
                    background: #1b3a4b;
                    color: #22d3a6;
                    border: 1px solid #22d3a6;
                    border-radius: 6px;
                    padding: 6px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #232a3d;
                    color: #e8ebf2;
                    border: 1px solid #2c3350;
                }
            """)
        else:
            self.btn_toggle_gps.setStyleSheet("""
                QPushButton {
                    background: #232a3d;
                    color: #e8ebf2;
                    border: 1px solid #2c3350;
                    border-radius: 6px;
                    padding: 6px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #2f3d6b;
                    border: 1px solid #5b8cff;
                }
            """)
            
        # Vô hiệu hóa nút Đi Tự Động nếu hết lượt hoặc kết thúc game
        if s["hint_uses"] <= 0 or s["game_over"]:
            self.btn_auto_step.setEnabled(False)
            self.btn_auto_step.setStyleSheet("""
                QPushButton {
                    background: #1b2030;
                    color: #8b93ad;
                    border: 1px solid #2c3350;
                    border-radius: 6px;
                    padding: 6px;
                    font-weight: bold;
                    font-size: 11px;
                }
            """)
        else:
            self.btn_auto_step.setEnabled(True)
            self.btn_auto_step.setStyleSheet("""
                QPushButton {
                    background: #232a3d;
                    color: #e8ebf2;
                    border: 1px solid #2c3350;
                    border-radius: 6px;
                    padding: 6px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #2f3d6b;
                    border: 1px solid #5b8cff;
                }
            """)

        # Cập nhật nút AND-OR
        self.btn_and_or.setEnabled(not s["game_over"])
        if s["game_over"]:
            self.btn_and_or.setStyleSheet("""
                QPushButton {
                    background: #1b2030;
                    color: #8b93ad;
                    border: 1px solid #2c3350;
                    border-radius: 6px;
                    padding: 6px;
                    font-weight: bold;
                    font-size: 11px;
                }
            """)
        else:
            self.btn_and_or.setStyleSheet("""
                QPushButton {
                    background: #232a3d;
                    color: #e8ebf2;
                    border: 1px solid #2c3350;
                    border-radius: 6px;
                    padding: 6px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #2f3d6b;
                    border: 1px solid #5b8cff;
                }
            """)

        # Cập nhật thông báo trạng thái
        if s["game_over"]:
            if s["won"]:
                self.status_msg.setText("🎉 THẮNG! Robot đã thoát hiểm!")
                self.status_msg.setStyleSheet("color: #22d3a6; font-weight: bold; font-size: 13px; margin-top: 4px; min-height: 20px;")
            else:
                self.status_msg.setText("💀 BẠN ĐÃ THUA! Bị bắt giữ!")
                self.status_msg.setStyleSheet("color: #ff6b6b; font-weight: bold; font-size: 13px; margin-top: 4px; min-height: 20px;")
        elif s["message"]:
            self.status_msg.setText(s["message"])
            self.status_msg.setStyleSheet("color: #ffd166; font-weight: bold; font-size: 11px; margin-top: 4px; min-height: 20px;")
        else:
            self.status_msg.setText("")


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(QSS)
    win = GameWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()