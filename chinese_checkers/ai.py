import random
import math
import time
from board import Board

_GOAL_TARGET_ROW = {'S': 16, 'N': 0}

# Pre-built: for each goal triangle, the "row depth" of each cell (deeper = better)
# S goal: rows 13-16, deepest is row 16. N goal: rows 0-3, deepest is row 0.
_GOAL_DEPTH = {}


def _build_goal_depths(board):
    global _GOAL_DEPTH
    if _GOAL_DEPTH:
        return
    for goal, positions in board.triangles.items():
        if goal == 'S':
            _GOAL_DEPTH[goal] = {pos: pos[0] - 13 for pos in positions}  # 0..3
        elif goal == 'N':
            _GOAL_DEPTH[goal] = {pos: 3 - pos[0] for pos in positions}   # 0..3


def _hex_dist(a, b):
    dr = a[0] - b[0]
    dc = (a[1] - b[1]) // 2
    if (dr > 0) == (dc > 0):
        return abs(dr) + abs(dc)
    return max(abs(dr), abs(dc))


class SmartAI:

    def __init__(self, game):
        self.game = game
        self.time_limit = 2.8
        self.ttable = {}
        self._recent_states = []
        self._max_history = 8
        _build_goal_depths(game.board)

    def choose_move(self):
        player = self.game.current_player
        board = self.game.board
        moves = self._get_all_moves(board, player)
        if not moves:
            return None
        if len(moves) == 1:
            self._record_history(board, player, moves[0])
            return moves[0]

        start_time = time.time()
        best_move_overall = moves[0]

        if len(self.ttable) > 300000:
            self.ttable.clear()

        previous_best_moves = []

        for max_depth in range(1, 14):
            self._search_aborted = False
            best_score = -math.inf
            best_moves_for_depth = []

            moves.sort(key=lambda m: self._quick_score(board, m, player), reverse=True)
            for pm in reversed(previous_best_moves):
                if pm in moves:
                    moves.remove(pm)
                    moves.insert(0, pm)

            for (from_pos, to_pos) in moves:
                if time.time() - start_time > self.time_limit:
                    self._search_aborted = True
                    break

                captured = board.grid[to_pos]
                board.move_piece(from_pos, to_pos)
                opponent = self._other_player(player)
                score = self._alphabeta(
                    board, max_depth - 1, -math.inf, math.inf,
                    False, player, opponent, start_time
                )
                board.move_piece(to_pos, from_pos)
                board.grid[to_pos] = captured

                if self._search_aborted:
                    break

                osc_penalty = self._oscillation_penalty(board, player, (from_pos, to_pos))
                score -= osc_penalty

                if score > best_score:
                    best_score = score
                    best_moves_for_depth = [(from_pos, to_pos)]
                elif score == best_score:
                    best_moves_for_depth.append((from_pos, to_pos))

            if self._search_aborted:
                break

            if best_moves_for_depth:
                best_move_overall = random.choice(best_moves_for_depth)
                previous_best_moves = best_moves_for_depth
                if best_score > 9500:
                    break

        self._record_history(board, player, best_move_overall)
        return best_move_overall

    def _record_history(self, board, player, move):
        if not move:
            return
        (from_pos, to_pos) = move
        board.move_piece(from_pos, to_pos)
        state = self._board_state_key(board, player)
        board.move_piece(to_pos, from_pos)
        board.grid[from_pos] = player.id
        self._recent_states.append(state)
        if len(self._recent_states) > self._max_history:
            self._recent_states.pop(0)

    def _alphabeta(self, board, depth, alpha, beta, is_maximizing,
                   max_player, min_player, start_time):
        if time.time() - start_time > self.time_limit:
            self._search_aborted = True
            return 0

        state_key = self._full_board_hash(board, is_maximizing)
        if state_key in self.ttable:
            (tt_depth, tt_score, tt_flag) = self.ttable[state_key]
            if tt_depth >= depth:
                if tt_flag == 'EXACT':
                    return tt_score
                elif tt_flag == 'LOWERBOUND':
                    alpha = max(alpha, tt_score)
                elif tt_flag == 'UPPERBOUND':
                    beta = min(beta, tt_score)
                if alpha >= beta:
                    return tt_score

        if depth == 0:
            score = self._evaluate(board, max_player, min_player)
            self.ttable[state_key] = (0, score, 'EXACT')
            return score

        current = max_player if is_maximizing else min_player
        moves = self._get_all_moves(board, current)
        if not moves:
            score = self._evaluate(board, max_player, min_player)
            self.ttable[state_key] = (depth, score, 'EXACT')
            return score

        moves.sort(key=lambda m: self._quick_score(board, m, current), reverse=True)

        alpha_orig = alpha
        beta_orig = beta
        value = -math.inf if is_maximizing else math.inf

        for (from_pos, to_pos) in moves:
            captured = board.grid[to_pos]
            board.move_piece(from_pos, to_pos)
            child = self._alphabeta(
                board, depth - 1, alpha, beta,
                not is_maximizing, max_player, min_player, start_time
            )
            board.move_piece(to_pos, from_pos)
            board.grid[to_pos] = captured

            if is_maximizing:
                value = max(value, child)
                alpha = max(alpha, value)
            else:
                value = min(value, child)
                beta = min(beta, value)

            if alpha >= beta or self._search_aborted:
                break

        if not self._search_aborted:
            if value <= alpha_orig:
                flag = 'UPPERBOUND'
            elif value >= beta_orig:
                flag = 'LOWERBOUND'
            else:
                flag = 'EXACT'
            self.ttable[state_key] = (depth, value, flag)

        return value

    # ── Evaluation ──────────────────────────────────────────────────────

    def _evaluate(self, board, max_player, min_player):
        (p1_score, p1_win) = self._score_player(board, max_player)
        if p1_win:
            return 10000
        (p2_score, p2_win) = self._score_player(board, min_player)
        if p2_win:
            return -10000
        return p1_score - p2_score

    def _score_player(self, board, player):
        goal = player.goal
        goal_set = board.triangles[goal]
        pieces = [pos for pos in board.all_positions if board.grid[pos] == player.id]
        if not pieces:
            return (-9999, False)

        in_goal = [p for p in pieces if p in goal_set]
        in_goal_count = len(in_goal)
        total = len(pieces)

        if in_goal_count == total:
            return (10000, True)

        goal_depths = _GOAL_DEPTH[goal]
        score = 0.0

        # --- Per-piece scores ---
        piece_set = set(pieces)
        row_progresses = []
        for pos in pieces:
            (r, c) = pos
            if goal == 'S':
                progress = r          # 0 (home) → 16 (goal)
            else:
                progress = 16 - r     # 0 (home) → 16 (goal)
            row_progresses.append(progress)

            # 1. Row advancement - the single most important factor
            score += progress * 12.0

            # 2. Centrality bonus for mid-board (col near 12 = more jump paths)
            dist_to_end = 16 - progress
            if dist_to_end > 4:
                score -= abs(c - 12) * 1.2

            # 3. Goal occupancy
            if pos in goal_set:
                depth_bonus = goal_depths.get(pos, 0)
                score += 80.0 + depth_bonus * 15.0
            else:
                # 4. Hex distance to nearest empty goal cell
                empty_goal = [g for g in goal_set if board.grid[g] is None]
                if empty_goal:
                    min_hdist = min(_hex_dist(pos, g) for g in empty_goal)
                    score -= min_hdist * 5.0
                    # Endgame urgency: once 6+ pieces inside, stragglers must rush
                    if in_goal_count >= 6:
                        urgency = 1.0 + math.exp(in_goal_count - 6)
                        score -= min_hdist * urgency

                # 7. Forward jump mobility: reward being in a position to jump forward
                for (dr, dc) in Board.DIRECTIONS:
                    is_forward = (goal == 'S' and dr >= 0) or (goal == 'N' and dr <= 0)
                    if not is_forward:
                        continue
                    (mr, mc) = (r + dr, c + dc)
                    (lr, lc) = (r + 2 * dr, c + 2 * dc)
                    if ((mr, mc) in board.all_positions
                            and board.grid.get((mr, mc)) is not None
                            and (lr, lc) in board.all_positions
                            and board.grid.get((lr, lc)) is None):
                        score += 12.0

        # 5. Straggler penalty: only punish pieces that lag behind the average
        if row_progresses:
            min_prog = min(row_progresses)
            avg_prog = sum(row_progresses) / len(row_progresses)

            # Penalty grows strongly as the game progresses (more in_goal = endgame)
            straggler_weight = 10.0 + in_goal_count * 4.0
            score -= (16 - min_prog) * straggler_weight

            # Lag penalty: only penalise pieces more than 4 rows behind average.
            # Leaders running ahead are NOT penalised, encouraging big jumps.
            lag = max(0.0, avg_prog - min_prog - 4.0)
            score -= lag * 10.0

        # 6. Formation / chain-jump bridge bonus
        # Weight kept low to avoid AI clustering pieces instead of making big jumps
        bridge_score = 0
        for pos in pieces:
            (r, c) = pos
            for (dr, dc) in Board.DIRECTIONS:
                if (r + dr, c + dc) in piece_set:
                    bridge_score += 1
        score += bridge_score * 3.0

        return (score, False)

    # ── Helpers ─────────────────────────────────────────────────────────

    def _oscillation_penalty(self, board, player, move):
        (from_pos, to_pos) = move
        board.move_piece(from_pos, to_pos)
        state = self._board_state_key(board, player)
        board.move_piece(to_pos, from_pos)
        board.grid[from_pos] = player.id

        penalty = 0
        for (i, prev) in enumerate(reversed(self._recent_states)):
            if state == prev:
                penalty += 200 * (1.0 + 2.0 / (i + 1))
        return penalty

    def _board_state_key(self, board, player):
        return tuple(sorted(pos for pos in board.all_positions if board.grid[pos] == player.id))

    def _full_board_hash(self, board, is_maximizing):
        p1 = tuple(sorted(pos for pos in board.all_positions if board.grid[pos] == 1))
        p2 = tuple(sorted(pos for pos in board.all_positions if board.grid[pos] == 2))
        return hash((p1, p2, is_maximizing))

    def _get_all_moves(self, board, player):
        moves = []
        for pos in board.all_positions:
            if board.grid[pos] != player.id:
                continue
            for dest in board.get_all_valid_moves(pos, goal_triangle=player.goal):
                moves.append((pos, dest))
        return moves

    def _quick_score(self, board, move, player):
        (from_pos, to_pos) = move
        goal = player.goal
        goal_set = board.triangles[goal]

        if goal == 'S':
            row_adv = to_pos[0] - from_pos[0]
        else:
            row_adv = from_pos[0] - to_pos[0]

        score = row_adv * 15

        # Strongly prefer larger jumps (chain-jump potential)
        jump_size = max(abs(to_pos[0] - from_pos[0]), abs(to_pos[1] - from_pos[1]))
        score += jump_size * 14

        # Extra bonus for actual multi-step jumps (row advance >= 2)
        if abs(to_pos[0] - from_pos[0]) >= 2:
            score += 35

        # Centrality
        score -= abs(to_pos[1] - 12) * 0.5

        # Strong bonus for entering goal
        if to_pos in goal_set and from_pos not in goal_set:
            score += 100

        # Bonus for going deeper into goal
        if to_pos in goal_set:
            depth_val = _GOAL_DEPTH[goal].get(to_pos, 0)
            score += depth_val * 20

        # Straggler bonus: heavily prioritise moving the most-behind piece
        piece_rows = []
        for pos in board.all_positions:
            if board.grid[pos] == player.id:
                piece_rows.append(pos[0] if goal == 'S' else 16 - pos[0])
        if piece_rows:
            min_row = min(piece_rows)
            from_prog = from_pos[0] if goal == 'S' else 16 - from_pos[0]
            if from_prog == min_row:
                score += 40

        return score

    def _other_player(self, player):
        return self.game.players[0] if player.id == self.game.players[1].id else self.game.players[1]