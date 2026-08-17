from typing import Callable, Optional

# Heuristic definition: a phase-based weighted evaluation function.
#
# 1. Positional score (all phases): each square has a strategic weight:
#    - corners: +100 (stable, can never be flipped)
#    - c-squares (edge squares adjacent to corners): -20 (size > 4) or -5 (size <= 4)
#      because they give opponent access to corners
#    - x-squares (diagonal to corners): -10 (size > 4) or +1 (size <= 4)
#    - edges: +10 (harder to flip)
#    - all other squares: +1
#
# 2. Mobility (mid-game only, boards size <= 6, 40%-85% full):
#    normalized difference in legal moves: 100 * (my_moves - opp_moves) / (my_moves + opp_moves)
#    encourages maximizing options while limiting opponent's options
#
# 3. Phase-based weighting:
#    - early game (< 40% full): positional score only (avoid costly mobility call)
#    - mid game (40%-85% full): positional score + mobility
#    - late game (>= 85% full): raw disk difference * 20 (maximize final count)

# These functions are imported for you to use
# in your implementation.
from src import (
    find_lines,
    get_possible_moves,
    get_score,
    play_move,
    eprint      # for debugging
)

# Use this global variable for state caching.
# You may find that it's useful to use the following
# information to form a key into the
#
#       (board, player_to_move, limit, node_type)
#
state_cache = {}


###############################################################################
############################# VALUE FUNCTIONS #################################
###############################################################################
def compute_utility(board: tuple[tuple[int, ...], ...], color: int) -> int:
    """
    Return the utility value of the given board for the given player color.

    :param board: a board representing the current state of an Othello game
    :param color: the color of the player. 1 for dark, 2 for light.

    :return: the utility of the given board for the given player color.
    """
    (score_dark, score_light) = get_score(board)
    if color == 1:
        return score_dark - score_light
    else:
        return score_light - score_dark

_weight_cache = {}

def get_position_weights(size):
    if size in _weight_cache:
        return _weight_cache[size]

    weights = [[1] * size for _ in range(size)]
    for r in range(size):
        for c in range(size):
            is_corner  = (r in (0, size-1)) and (c in (0, size-1))
            is_c_square = ((r in (0, size-1)) and (c in (1, size-2))) or \
                          ((c in (0, size-1)) and (r in (1, size-2)))
            is_x_square = (r in (1, size-2)) and (c in (1, size-2))
            is_edge    = r in (0, size-1) or c in (0, size-1)

            if is_corner:
                weights[r][c] = 100
            elif is_c_square:
                weights[r][c] = -20 if size > 4 else -5
            elif is_x_square:
                weights[r][c] = -10 if size > 4 else 1
            elif is_edge:
                weights[r][c] = 10

    _weight_cache[size] = weights
    return weights

def compute_heuristic(board, color):
    size = len(board)
    opp = 3 - color
    weights = get_position_weights(size)

    pos_score = 0
    my_disks = 0
    opp_disks = 0
    empty = 0

    for r in range(size):
        for c in range(size):
            cell = board[r][c]
            if cell == color:
                pos_score += weights[r][c]
                my_disks += 1
            elif cell == opp:
                pos_score -= weights[r][c]
                opp_disks += 1
            else:
                empty += 1

    total = my_disks + opp_disks
    completion = total / (size * size)

    if completion < 0.4:
        return int(pos_score)

    if completion >= 0.85:
        return (my_disks - opp_disks) * 20
    
    if size <= 6 and 0.4 <= completion < 0.85:
        my_moves = len(get_possible_moves(board, color))
        opp_moves = len(get_possible_moves(board, opp))
        if my_moves == 0 and opp_moves == 0:
            return 10000 if my_disks > opp_disks else -10000
        mobility = 100 * (my_moves - opp_moves) / max(1, my_moves + opp_moves)
        return int(pos_score + mobility)
    else:
        return int(pos_score)

###############################################################################
####################### ALPHA-BETA PRUNING FUNCTIONS ##########################
###############################################################################
def alphabeta_min_node(
        value_fn: Callable,
        board: tuple[tuple[int, ...], ...],
        color: int,
        alpha: int,
        beta: int,
        limit: int,
        caching: int = 0,
        ordering: int = 0) -> tuple[Optional[tuple[int, int]], int]:
    """
    Return a tuple of the move that yields the *lowest* possible utility
    and the *lowest* possible utility itself for the given board, color,
    limit, value_fn to determine utility and alpha, beta to prune.
    Optionally use state caching and node ordering.

    :param value_fn: function used to determine utility values
    :param board: the current state of the Othello game
    :param color: the color of the current player (1 for dark, 2 for light)
    :param alpha: the alpha parameter, used in pruning
    :param beta: the beta parameter, used in pruning
    :param limit: the depth limit of the alpha-beta search
    :param caching: whether to use state caching
                    if 1, use state caching
                    if 0, do not use state caching
    :param ordering: whether to order moves during move selection

    :return: a tuple (None|(i,j), utility) of the next move to be
             taken, and the utility value associated with it
    """
    key = (board, color, limit, "min")
    if caching and key in state_cache:
        return state_cache[key]
    opponent_color = 3 - color
    moves = get_possible_moves(board, opponent_color)
    if not moves or limit == 0:
        result = (None, value_fn(board, color))
        if caching:
            state_cache[key] = result
        return result
    else:
        if ordering:
            moves = sorted(moves, key=lambda move: value_fn(play_move(board, opponent_color, move[0], move[1]), color))

        best_move = None
        best_utility = float('inf')
        for move in moves:
            new_board = play_move(board, opponent_color, move[0], move[1])
            _, utility = alphabeta_max_node(value_fn, new_board, color, alpha, beta, limit - 1, caching, ordering)
            
            if utility < best_utility:
                best_utility = utility
                best_move = move
            beta = min(beta, best_utility)
            if beta <= alpha:
                break

        result = (best_move, best_utility)
        if caching:
            state_cache[key] = result
        return result

def alphabeta_max_node(
        value_fn: Callable,
        board: tuple[tuple[int, ...], ...],
        color: int,
        alpha: int,
        beta: int,
        limit: int,
        caching: int = 0,
        ordering: int = 0) -> tuple[Optional[tuple[int, int]], int]:
    """
    Return a tuple of the move that yields the *highest* possible utility
    and the *highest* possible utility itself for the given board, color,
    limit, value_fn to determine utility and alpha, beta to prune.
    Optionally use state caching and node ordering.

    :param value_fn: function used to determine utility values
    :param board: the current state of the Othello game
    :param color: the color of the current player (1 for dark, 2 for light)
    :param alpha: the alpha parameter, used in pruning
    :param beta: the beta parameter, used in pruning
    :param limit: the depth limit of the alpha-beta search
    :param caching: whether to use state caching
                    if 1, use state caching
                    if 0, do not use state caching
    :param ordering: whether to order moves during move selection

    :return: a tuple (None|(i,j), utility) of the next move to be
             taken, and the utility value associated with it
    """
    key = (board, color, limit, "max")
    if caching and key in state_cache:
        return state_cache[key]
    moves = get_possible_moves(board, color)
    if not moves or limit == 0:
        result = (None, value_fn(board, color))
        if caching:
            state_cache[key] = result
        return result
    else:
        if ordering:
            moves = sorted(moves, key=lambda move: value_fn(play_move(board, color, move[0], move[1]), color), reverse=True)

        best_move = None
        best_utility = float('-inf')
        for move in moves:
            new_board = play_move(board, color, move[0], move[1])
            _, utility = alphabeta_min_node(value_fn, new_board, color, alpha, beta, limit - 1, caching, ordering)
            
            if utility > best_utility:
                best_utility = utility
                best_move = move
            alpha = max(alpha, best_utility)
            if beta <= alpha:
                break
        result = (best_move, best_utility)
        if caching:
            state_cache[key] = result
        return result

def select_move_alphabeta(
        value_fn: Callable,
        board: tuple[tuple[int, ...], ...],
        color: int,
        limit: int = -1,
        caching: int = 0,
        ordering: int = 0) -> Optional[tuple[int, int]]:
    """
    Return the next move determined by alpha-beta pruning in a game of Othello
    defined by the given board, player color, depth limit, and use of caching
    and node ordering. Use value_fn to determine utility values in subroutines.

    :param value_fn: function used to determine utility values
    :param board: the current state of the Othello game
    :param color: the color of the current player (1 for dark, 2 for light)
    :param limit: the depth limit of the alpha-beta search
    :param caching: whether to use state caching
                    if 1, use state caching
                    if 0, do not use state caching
    :param ordering: whether to order moves during move selection

    :return: a tuple (i, j) of the next move to be taken, or None
    """
    if limit < 0 or limit is None:
        limit = float("inf")
    move, _ = alphabeta_max_node(value_fn, board, color, float('-inf'), float('inf'), limit, caching, ordering)
    return move


###############################################################################
############################# MINIMAX FUNCTIONS ###############################
###############################################################################
def minimax_min_node(
        value_fn: Callable,
        board: tuple[tuple[int, ...], ...],
        color: int,
        limit: int,
        caching: int = 0) -> tuple[Optional[tuple[int, int]], int]:
    """
    Return a tuple of the move that yields the lowest possible utility
    and the lowest possible utility itself for the given board, color,
    limit, using value_fn to determine utility. Optionally use state caching
    and node ordering.

    The algorithm is outlined as follows:
        1. Get all allowed moves
        2. Check if we are at a terminal state
        3. If not, minimize over the set of max utility values for each possible move

    :param value_fn: function used to determine utility values
    :param board: the current state of the Othello game
    :param color: the color of the current player (1 for dark, 2 for light)
    :param limit: the depth limit of the Minimax search
    :param caching: whether to use state caching in Minimax
                    if 1, use state caching
                    if 0, do not use state caching

    :return: a tuple (None|(i,j), utility) of the next move to be
             taken, and the utility value associated with it
    """
    key = (board, color, limit, "min")
    if caching and key in state_cache:  
        return state_cache[key]
    opponent_color = 3 - color
    moves = get_possible_moves(board, opponent_color)
    if not moves or limit == 0:
        result = (None, value_fn(board, color))
        if caching:
            state_cache[key] = result
        return result
    else:
        best_move = None
        best_utility = float('inf')
        for move in moves:
            new_board = play_move(board, opponent_color, move[0], move[1])
            _, utility = minimax_max_node(value_fn, new_board, color, limit - 1, caching)
            
            if utility < best_utility:
                best_utility = utility
                best_move = move
        result = (best_move, best_utility)
        if caching:
            state_cache[key] = result
        return result

def minimax_max_node(
        value_fn: Callable,
        board: tuple[tuple[int, ...], ...],
        color: int,
        limit: int,
        caching: int = 0) -> tuple[Optional[tuple[int, int]], int]:
    """
    Return a tuple of the move that yields the highest possible utility
    and the highest possible utility itself for the given board, color,
    limit, using value_fn to determine utility. Optionally use state caching
    and node ordering.

    The algorithm is outlined as follows:
        1. Get all allowed moves
        2. Check if we are at a terminal state
        3. If not, maximize over the set of min utility values for each possible move

    :param value_fn: function used to determine utility values
    :param board: the current state of the Othello game
    :param color: the color of the current player (1 for dark, 2 for light)
    :param limit: the depth limit of the Minimax search
    :param caching: whether to use state caching in Minimax
                    if 1, use state caching
                    if 0, do not use state caching

    :return: a tuple (None|(i,j), utility) of the next move to be
             taken, and the utility value associated with it
    """
    key = (board, color, limit, "max")
    if caching and key in state_cache:
        return state_cache[key]
    moves = get_possible_moves(board, color)
    if not moves or limit == 0:
        result = (None, value_fn(board, color))
        if caching:
            state_cache[key] = result
        return result
    else:
        best_move = None
        best_utility = float('-inf')
        for move in moves:
            new_board = play_move(board, color, move[0], move[1])
            _, utility = minimax_min_node(value_fn, new_board, color, limit - 1, caching)
            
            if utility > best_utility:
                best_utility = utility
                best_move = move
        result = (best_move, best_utility)
        if caching:
            state_cache[key] = result
        return result

def select_move_minimax(
        value_fn: Callable,
        board: tuple[tuple[int, ...], ...],
        color: int,
        limit: int,
        caching: int = 0) -> Optional[tuple[int, int]]:
    """
    Return the next move determined by Minimax in a game of Othello
    defined by the given board, player color, depth limit, and use of caching.
    Uses value_fn to determine utility values in subroutines.

    :param value_fn: function used to determine utility values
    :param board: the current state of the Othello game
    :param color: the color of the current player (1 for dark, 2 for light)
    :param limit: the depth limit of the Minimax search
    :param caching: whether to use state caching
                    if 1, use state caching
                    if 0, do not use state caching

    :return: a tuple (i, j) of the next move to be taken, or None
    """
    if limit < 0 or limit is None:
        limit = float("inf")
    move, _ = minimax_max_node(value_fn, board, color, limit, caching)
    return move

###############################################################################
############################### ENTRY-POINT ###################################
###############################################################################
def run_ai():
    """
    Communicate with the game manager to simulate a player in a game
    of Othello. Accepts input from stdin to determine:
        * color    - 1 for dark, 2 for light
        * limit    - the depth limit
        * minimax  - 1 to run minimax, otherwise run alpha-beta
        * caching  - 1 to run with caching, otherwise run without it
        * ordering - 1 to run alpha-beta with node ordering,
                     otherwise run without it.

    Use `compute_utility` as the value function by default.
    """
    print("tanya_better")  # First line is the name of this AI
    color, limit, minimax, caching, ordering = map(int, input().split(","))

    eprint("Running MINIMAX") if minimax else eprint("Running ALPHA-BETA")
    eprint("State Caching is ON") if caching else eprint("State Caching is OFF")
    eprint("Node Ordering is ON") if ordering else eprint("Node Ordering is OFF")
    eprint("Depth Limit is ", limit) if limit >= 0 else eprint("Depth Limit is OFF")

    while True:
        # Read the current state of the game as yielded by the game manager.
        # Consists of a string of the form:
        #
        #       (SCORE|FINAL) \d+ \d+    , e.g. SCORE 9 7
        #
        # The first string is the state of the game:
        #   * SCORE indicates that the game is still active.
        #   * FINAL indicates that the game is over.
        #
        # The first digit is the score for player 1 (the dark player.)
        #
        # The second digit is the score for player 2 (the light player.)
        status, _, _ = input().strip().split()

        if status == "FINAL":
            break
        else:
            # Read the current board represented as a tuple of tuples, where
            # nested tuples represent rows of the board. For example:
            #
            #   ((0, 0, 0, 0),
            #    (0, 2, 1, 0),
            #    (0, 1, 2, 0),
            #    (0, 0, 0, 0))
            #
            # where
            #
            #   * 0 - an empty square on the board
            #   * 1 - a piece played by player 1, or the dark player.
            #   * 2 - a piece played by player 2, or the light player.
            board = eval(input())

            if (minimax == 1):
                i, j = select_move_minimax(
                    compute_utility,
                    board,
                    color,
                    limit,
                    caching
                )
            else:
                i, j = select_move_alphabeta(
                    compute_utility,
                    board,
                    color,
                    limit,
                    caching,
                    ordering
                )

            print("{} {}".format(i, j))


if __name__ == "__main__":
    run_ai()
