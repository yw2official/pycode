import math
import tkinter as tk
from tkinter import font as tkfont
from board import Board
from game import Game
from ai import SmartAI
BG_DARK = '#0f1923'
BG_PANEL = '#162029'
BG_CANVAS = '#1a2634'
HOLE_EMPTY = '#2a3a4a'
HOLE_BORDER = '#3a4f63'
HIGHLIGHT_SEL = '#f1c40f'
HIGHLIGHT_MOVE = '#2ecc71'
LINE_COLOR = '#1e2e3e'
TEXT_PRIMARY = '#ffffff'
TEXT_SECONDARY = '#ffeaa7'
BTN_BG = '#2979ff'
BTN_FG = '#ffffff'
BTN_ACTIVE = '#448aff'
TRIANGLE_TINTS = {'N': '#3d1a1a', 'S': '#1a2a3d', 'NW': '#2d2d1a', 'NE': '#1a2d1a', 'SW': '#2d1a2d', 'SE': '#1a2d2d'}
PLAYER_COLORS = {1: ('#3498db', '#2980b9', '#a0c4f5'), 2: ('#e74c3c', '#c0392b', '#f5a6a0')}
CELL_SIZE = 26
MARGIN_X = 55
MARGIN_Y = 45
PIECE_R = 11
HOLE_R = 5
CANVAS_W = MARGIN_X * 2 + 24 * CELL_SIZE
CANVAS_H = MARGIN_Y * 2 + int(16 * CELL_SIZE * math.sqrt(3))
PANEL_W = 220

class ChineseCheckersGUI:

    def __init__(self, root):
        self.root = root
        self.root.title('跳棋 — Chinese Checkers')
        self.root.configure(bg=BG_DARK)
        self.root.resizable(False, False)
        self.game = Game()
        self.ai = SmartAI(self.game)
        self.ai_mode = False
        self._title_font = tkfont.Font(family='Helvetica', size=16, weight='bold')
        self._label_font = tkfont.Font(family='Helvetica', size=12)
        self._btn_font = tkfont.Font(family='Helvetica', size=11)
        self._status_font = tkfont.Font(family='Helvetica', size=11)
        self._build_ui()
        self._draw_board()

    def _build_ui(self):
        main = tk.Frame(self.root, bg=BG_DARK)
        main.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(main, width=CANVAS_W, height=CANVAS_H, bg=BG_CANVAS, highlightthickness=0)
        self.canvas.pack(side='left', padx=(10, 0), pady=10)
        self.canvas.bind('<Button-1>', self._on_click)
        panel = tk.Frame(main, width=PANEL_W, bg=BG_PANEL)
        panel.pack(side='right', fill='y', padx=10, pady=10)
        panel.pack_propagate(False)
        tk.Label(panel, text='跳  棋', font=self._title_font, bg=BG_PANEL, fg=TEXT_PRIMARY).pack(pady=(20, 5))
        tk.Label(panel, text='Chinese Checkers', font=self._label_font, bg=BG_PANEL, fg=TEXT_SECONDARY).pack(pady=(0, 20))
        tk.Frame(panel, height=1, bg='#3a4f63').pack(fill='x', padx=15, pady=5)
        self.player_frame = tk.Frame(panel, bg=BG_PANEL)
        self.player_frame.pack(pady=10)
        self.player_dot = tk.Canvas(self.player_frame, width=22, height=22, bg=BG_PANEL, highlightthickness=0)
        self.player_dot.pack(side='left', padx=(0, 8))
        self.player_label = tk.Label(self.player_frame, text='', font=self._label_font, bg=BG_PANEL, fg=TEXT_PRIMARY)
        self.player_label.pack(side='left')
        self.status_label = tk.Label(panel, text='', font=self._status_font, bg=BG_PANEL, fg=TEXT_SECONDARY, wraplength=190, justify='center')
        self.status_label.pack(pady=(5, 15))
        tk.Frame(panel, height=1, bg='#3a4f63').pack(fill='x', padx=15, pady=5)
        btn_defs = [('结束跳跃', self._on_end_jump), ('悔  棋', self._on_undo), ('重新开始', self._on_restart)]
        self.buttons = {}
        for (text, cmd) in btn_defs:
            btn = self._make_btn(panel, text, cmd, BTN_BG, BTN_FG, BTN_ACTIVE)
            btn.pack(pady=4, padx=20, fill='x')
            self.buttons[text] = btn
        tk.Frame(panel, height=1, bg='#3a4f63').pack(fill='x', padx=15, pady=10)
        tk.Label(panel, text='游戏模式', font=self._label_font, bg=BG_PANEL, fg=TEXT_PRIMARY).pack(pady=(5, 5))
        self.mode_var = tk.StringVar(value='pvp')
        for (text, val) in [('双人对战', 'pvp'), ('人机对战', 'pvai')]:
            tk.Radiobutton(panel, text=text, variable=self.mode_var, value=val, font=self._status_font, bg=BG_PANEL, fg='#ffffff', selectcolor=BG_DARK, activebackground=BG_PANEL, activeforeground='#ffffff', command=self._on_mode_change).pack(anchor='w', padx=40)
        tk.Frame(panel, bg=BG_PANEL).pack(fill='both', expand=True)
        quit_btn = self._make_btn(panel, '退出游戏', self.root.quit, '#922b21', '#ffffff', '#c0392b')
        quit_btn.pack(pady=(0, 20), padx=20, fill='x')
        self._update_status()

    def _make_btn(self, parent, text, command, bg, fg, active_bg):
        frame = tk.Frame(parent, bg=bg, cursor='hand2', padx=2, pady=6)
        label = tk.Label(frame, text=text, font=self._btn_font, bg=bg, fg=fg)
        label.pack()

        def on_enter(e):
            if frame.cget('cursor') == 'hand2':
                frame.config(bg=active_bg)
                label.config(bg=active_bg)

        def on_leave(e):
            if frame.cget('cursor') == 'hand2':
                frame.config(bg=bg)
                label.config(bg=bg)

        def on_click(e):
            if frame.cget('cursor') != 'hand2':
                return
            frame.config(bg='#888888')
            label.config(bg='#888888')
            frame.after(120, lambda : (frame.config(bg=bg), label.config(bg=bg)))
            frame.after(50, command)
        frame.bind('<Enter>', on_enter)
        frame.bind('<Leave>', on_leave)
        frame.bind('<Button-1>', on_click)
        label.bind('<Enter>', on_enter)
        label.bind('<Leave>', on_leave)
        label.bind('<Button-1>', on_click)
        frame._btn_bg = bg
        frame._btn_fg = fg
        frame._btn_label = label
        return frame

    def _set_btn_state(self, btn_frame, enabled):
        if enabled:
            btn_frame.config(bg=btn_frame._btn_bg, cursor='hand2')
            btn_frame._btn_label.config(bg=btn_frame._btn_bg, fg=btn_frame._btn_fg)
        else:
            btn_frame.config(bg='#444444', cursor='arrow')
            btn_frame._btn_label.config(bg='#444444', fg='#777777')

    def _pos_to_pixel(self, r, c):
        x = MARGIN_X + c * CELL_SIZE
        y = MARGIN_Y + r * CELL_SIZE * math.sqrt(3)
        return (x, y)

    def _pixel_to_pos(self, px, py):
        best = None
        best_dist = PIECE_R + 6
        for pos in self.game.board.all_positions:
            (x, y) = self._pos_to_pixel(*pos)
            d = math.hypot(px - x, py - y)
            if d < best_dist:
                best_dist = d
                best = pos
        return best

    def _draw_board(self):
        self.canvas.delete('all')
        self._draw_triangle_zones()
        drawn_edges = set()
        for pos in self.game.board.all_positions:
            (r, c) = pos
            (px, py) = self._pos_to_pixel(r, c)
            for (dr, dc) in Board.DIRECTIONS:
                nb = (r + dr, c + dc)
                if nb in self.game.board.all_positions:
                    edge = (min(pos, nb), max(pos, nb))
                    if edge not in drawn_edges:
                        drawn_edges.add(edge)
                        (nx, ny) = self._pos_to_pixel(*nb)
                        self.canvas.create_line(px, py, nx, ny, fill=LINE_COLOR, width=1)
        for pos in self.game.board.all_positions:
            (r, c) = pos
            (px, py) = self._pos_to_pixel(r, c)
            occupant = self.game.board.grid[pos]
            if occupant is not None:
                self._draw_piece(px, py, occupant, pos)
            else:
                self.canvas.create_oval(px - HOLE_R, py - HOLE_R, px + HOLE_R, py + HOLE_R, fill=HOLE_EMPTY, outline=HOLE_BORDER, width=1)
        if self.game.selected_pos is not None:
            (sx, sy) = self._pos_to_pixel(*self.game.selected_pos)
            self.canvas.create_oval(sx - PIECE_R - 3, sy - PIECE_R - 3, sx + PIECE_R + 3, sy + PIECE_R + 3, outline=HIGHLIGHT_SEL, width=3, dash=(4, 2))
        for mv in self.game.valid_moves:
            (mx, my) = self._pos_to_pixel(*mv)
            r_size = PIECE_R - 2
            self.canvas.create_oval(mx - r_size, my - r_size, mx + r_size, my + r_size, fill='', outline=HIGHLIGHT_MOVE, width=2, dash=(3, 3))
            self.canvas.create_oval(mx - 3, my - 3, mx + 3, my + 3, fill=HIGHLIGHT_MOVE, outline='')
        self._update_status()

    def _draw_piece(self, x, y, player_id, pos):
        (main_c, dark_c, light_c) = PLAYER_COLORS[player_id]
        r = PIECE_R
        self.canvas.create_oval(x - r + 1, y - r + 2, x + r + 1, y + r + 2, fill='#0a0a0a', outline='')
        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=main_c, outline=dark_c, width=1)
        hr = r // 3
        self.canvas.create_oval(x - hr - 1, y - hr - 2, x + hr - 1, y + hr - 2, fill=light_c, outline='')

    def _draw_triangle_zones(self):
        for (name, positions) in self.game.board.triangles.items():
            color = TRIANGLE_TINTS.get(name, '#1a2634')
            for pos in positions:
                (px, py) = self._pos_to_pixel(*pos)
                sz = CELL_SIZE * 0.8
                self.canvas.create_oval(px - sz, py - sz, px + sz, py + sz, fill=color, outline='', stipple='gray25')

    def _update_status(self):
        player = self.game.current_player
        self.player_dot.delete('all')
        self.player_dot.create_oval(3, 3, 19, 19, fill=player.color, outline='')
        self.player_label.config(text=player.name)
        self.status_label.config(text=self.game.status_text)
        self._set_btn_state(self.buttons['结束跳跃'], self.game.state == Game.CHAIN_JUMPING)
        self._set_btn_state(self.buttons['悔  棋'], bool(self.game.move_history) and self.game.state != Game.CHAIN_JUMPING)

    def _on_click(self, event):
        pos = self._pixel_to_pos(event.x, event.y)
        if pos is None:
            return
        if self.game.select(pos):
            self._draw_board()
            if not self.game.game_over and self.game.current_player.is_ai and (self.game.state == Game.IDLE):
                self.root.after(400, self._ai_turn)

    def _on_end_jump(self):
        if self.game.end_jump():
            self._draw_board()
            if not self.game.game_over and self.game.current_player.is_ai and (self.game.state == Game.IDLE):
                self.root.after(400, self._ai_turn)

    def _on_undo(self):
        if self.game.undo():
            self._draw_board()

    def _on_restart(self):
        self.ai_mode = self.mode_var.get() == 'pvai'
        self.game.reset(ai_mode=self.ai_mode)
        self._draw_board()
        if not self.game.game_over and self.game.current_player.is_ai and (self.game.state == Game.IDLE):
            self.root.after(500, self._ai_turn)

    def _on_mode_change(self):
        self._on_restart()

    def _ai_turn(self):
        if self.game.game_over or not self.game.current_player.is_ai:
            return
        move = self.ai.choose_move()
        if move is None:
            return
        (from_pos, to_pos) = move
        self.game.select(from_pos)
        self._draw_board()

        def do_move():
            self.game.select(to_pos)
            if self.game.state == Game.CHAIN_JUMPING:
                self.game.end_jump()
            self._draw_board()
        self.root.after(300, do_move)