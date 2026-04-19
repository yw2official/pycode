"""
Game logic for Chinese Checkers.

Manages players, turns, chain-jump state machine, win detection,
undo/redo, and game reset.
"""

from board import Board


class Player:
    """Represents a player in the game."""

    def __init__(self, pid, name, home, goal, color, is_ai=False):
        self.id = pid
        self.name = name
        self.home = home      # triangle where pieces start
        self.goal = goal      # triangle to fill for winning
        self.color = color    # display color
        self.is_ai = is_ai


class Game:
    """Chinese Checkers game controller."""

    # Game states
    IDLE = 'idle'
    PIECE_SELECTED = 'piece_selected'
    CHAIN_JUMPING = 'chain_jumping'

    def __init__(self):
        self.board = Board()
        self.players = []
        self.current_player_idx = 0
        self.state = self.IDLE
        self.selected_pos = None
        self.valid_moves = []
        self.jumping_from = None       # position being chain-jumped from
        self.jump_visited = set()      # visited positions during chain jump
        self.move_history = []         # stack of (from, to, player_idx) for undo
        self.game_over = False
        self.winner = None
        self._setup_two_players()

    # ── Setup ──────────────────────────────────────────────────────────

    def _setup_two_players(self):
        """Configure a 2-player game (N vs S)."""
        self.players = [
            Player(1, '玩家 1', 'S', 'N', '#3498db'),   # blue, bottom→top (moves first)
            Player(2, '玩家 2', 'N', 'S', '#e74c3c'),   # red, top→bottom
        ]
        self.board.clear()
        for p in self.players:
            self.board.setup_pieces(p.id, p.home)

    def reset(self, ai_mode=False):
        """Reset the game to initial state."""
        self.board.clear()
        self.players[1].is_ai = ai_mode
        self.players[1].name = '电脑' if ai_mode else '玩家 2'
        for p in self.players:
            self.board.setup_pieces(p.id, p.home)
        self.current_player_idx = 0
        self.state = self.IDLE
        self.selected_pos = None
        self.valid_moves = []
        self.jumping_from = None
        self.jump_visited = set()
        self.move_history = []
        self.game_over = False
        self.winner = None

    # ── Properties ─────────────────────────────────────────────────────

    @property
    def current_player(self):
        return self.players[self.current_player_idx]

    @property
    def status_text(self):
        if self.game_over:
            return f'🎉 {self.winner.name} 获胜!'
        if self.state == self.CHAIN_JUMPING:
            return f'{self.current_player.name} 连续跳跃中 (可点击继续跳或结束)'
        if self.state == self.PIECE_SELECTED:
            return f'{self.current_player.name} 已选棋子，请选择目标位置'
        return f'轮到 {self.current_player.name}，请选择棋子'

    # ── Interaction ────────────────────────────────────────────────────

    def select(self, pos):
        """Handle a click on board position *pos*.

        Returns True if the board state changed and needs redrawing.
        """
        if self.game_over:
            return False

        # ── Chain-jumping state: only allow continuing jump or deselect ──
        if self.state == self.CHAIN_JUMPING:
            if pos in self.valid_moves:
                self._execute_move(self.jumping_from, pos)
                return True
            return False

        # ── Piece-selected state ──
        if self.state == self.PIECE_SELECTED:
            # Click on valid destination → move
            if pos in self.valid_moves:
                self._execute_move(self.selected_pos, pos)
                return True
            # Click on another own piece → re-select
            if self.board.grid.get(pos) == self.current_player.id:
                self._select_piece(pos)
                return True
            # Click elsewhere → deselect
            self.state = self.IDLE
            self.selected_pos = None
            self.valid_moves = []
            return True

        # ── Idle state: select own piece ──
        if self.board.grid.get(pos) == self.current_player.id:
            self._select_piece(pos)
            return True

        return False

    def end_jump(self):
        """End a chain jump early (player chooses to stop)."""
        if self.state != self.CHAIN_JUMPING:
            return False
        self._finish_turn()
        return True

    def undo(self):
        """Undo the last completed move."""
        if not self.move_history or self.state == self.CHAIN_JUMPING:
            return False
        from_pos, to_pos, player_idx = self.move_history.pop()
        self.board.move_piece(to_pos, from_pos)
        self.current_player_idx = player_idx
        self.state = self.IDLE
        self.selected_pos = None
        self.valid_moves = []
        self.game_over = False
        self.winner = None
        return True

    # ── Internal helpers ───────────────────────────────────────────────

    def _select_piece(self, pos):
        """Select a piece and compute its valid moves."""
        player = self.current_player
        self.selected_pos = pos
        self.valid_moves = self.board.get_all_valid_moves(pos, goal_triangle=player.goal)
        self.state = self.PIECE_SELECTED

    def _execute_move(self, from_pos, to_pos):
        """Execute a move and update state (may enter chain-jump)."""
        is_jump = Board.is_jump(from_pos, to_pos)

        if self.state == self.CHAIN_JUMPING:
            # Continuing a chain: update the existing history entry's destination
            if self.move_history:
                orig_from, _, pidx = self.move_history.pop()
                self.move_history.append((orig_from, to_pos, pidx))
        else:
            # First move of the turn: record origin → destination
            self._chain_origin_pos = from_pos
            self.move_history.append((from_pos, to_pos, self.current_player_idx))

        self.board.move_piece(from_pos, to_pos)

        if is_jump:
            self.jump_visited.add(from_pos)
            self.jump_visited.add(to_pos)
            # Check for further jumps
            player = self.current_player
            further = self.board.get_single_jumps(to_pos)
            # Filter: cannot revisit, must stay in goal if already inside
            goal_set = self.board.triangles.get(player.goal, set())
            in_goal = to_pos in goal_set
            further = [j for j in further
                       if j not in self.jump_visited
                       and (not in_goal or j in goal_set)]
            if further:
                self.state = self.CHAIN_JUMPING
                self.jumping_from = to_pos
                self.selected_pos = to_pos
                self.valid_moves = further
                return
        self._finish_turn()

    def _finish_turn(self):
        """End the current turn, check for win, advance to next player."""
        player = self.current_player
        self.state = self.IDLE
        self.selected_pos = None
        self.valid_moves = []
        self.jumping_from = None
        self.jump_visited = set()

        if self._check_win(player):
            self.game_over = True
            self.winner = player
        else:
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

    def _check_win(self, player):
        """Check if all positions in the goal triangle are occupied by player."""
        goal_positions = self.board.triangles[player.goal]
        return all(self.board.grid[pos] == player.id for pos in goal_positions)
