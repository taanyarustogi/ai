"""
General notes to consider:
    * The input to these model-generating functions is shaped
      like the following example:

            e.g.
                 [[0,>,0,.,2],
                  [0,.,0,.,0],
                  [0,.,0,<,0]]

            0             -  an empty cell
            .             -  no inequality constraint
            <             -  left cell less than right cell
            >             -  left cell greater than rightcell
            range(1,n+1)  -  pre-set value at this position

      This grid represents the following Futoshiki board:

            e.g.
                -------------
                | _ > _ | 2 |
                | _ | _ | _ |
                | _ | _ < _ |
                -------------

      Note that the input is hence a list of lists where each inner list
      of length 2n - 1 represents a row of the board, where n is the dimension
      of the board.

    * Both models return a tuple (csp, variables):

      csp        - the CSP object representing the Futoshiki game
      variables  - a list of lists of variables corresponding to the
                   solved variables for csp. This list of lists is how
                   the solution to the csp is accessed.

    * An example of how models can be used in conjunction with the
      provided backend:

            e.g.
                 csp, variables = futoshiki_csp_model_1(board)
                 solver = BT(csp)
                 solver.bt_search(prop_FC)

      Upon completion of search, `variables[0][0].get_assigned_value()`
      will return the correct value in the top-left cell of the Futoshiki board.

"""
from typing import Any
from src import Variable, Constraint, CSP, BacktrackingSearch
from itertools import permutations

PERM_CACHE = {}


def futoshiki_csp_model_1(grid: list[list[Any]]) -> tuple['CSP', list[list['Variable']]]:
    """
    Return a tuple consisting of the constraint satisfaction problem constructed
    according to the input Futoshiki puzzle grid, and a list of lists of Variable
    objects that represents the matrix of values corresponding to the input grid
    indexed from (0, 0) to (n-1, n-1).

    Constraints for model 1 are built using only binary inequality for both rows
    and columns. That is, all constraints are fixed to two variables in scope.

    :param grid: a list of lists of objects representing the Futoshiki grid, e.g.
                    grid = [[0,>,0,.,2], [0,.,0,.,0], [0,.,0,<,0]]
    """
    dimension = len(grid)
    variables = []
    inequalities = []
    for row in range(dimension):
        row_variables = []
        for col in range(dimension):
            cell = grid[row][col*2]
            if cell == 0:
                variable = Variable(f"V{row}{col}", list(range(1, dimension + 1)))
            else:
                variable = Variable(f"V{row}{col}", [cell])
            row_variables.append(variable)

            if col < dimension - 1:
                token = grid[row][col*2 + 1]
                if token != '.':
                    inequalities.append((token, row, col))
        variables.append(row_variables)

    csp = CSP("Futoshiki")
    for row in range(dimension):
        for col in range(dimension):
            csp.add_var(variables[row][col])

    # every row has to have different values
    for row in range(dimension):
        for col in range(dimension):
            for var2 in range(col + 1, dimension):
                variable1 = variables[row][col]
                variable2 = variables[row][var2]
                constraint = Constraint(f"row{row}{col}{var2}", [variable1, variable2])
                constraint.add_satisfying_tuples([(a, b) for a in variable1.domain() for b in variable2.domain() if a != b])
                csp.add_constraint(constraint)

    # every column has to have different values
    for col in range(dimension):
        for row in range(dimension):
            for var2 in range(row + 1, dimension):
                variable1 = variables[row][col]
                variable2 = variables[var2][col]
                constraint = Constraint(f"col{col}{row}{var2}", [variable1, variable2])
                constraint.add_satisfying_tuples([(a, b) for a in variable1.domain() for b in variable2.domain() if a != b])
                csp.add_constraint(constraint)

    # add inequality constraints
    for token, row, col in inequalities:
        variable1 = variables[row][col]
        variable2 = variables[row][col + 1]
        constraint = Constraint(f"ineq{row}{col}", [variable1, variable2])
        if token == '>':
            constraint.add_satisfying_tuples([(a, b) for a in variable1.domain() for b in variable2.domain() if a > b])
        elif token == '<':
            constraint.add_satisfying_tuples([(a, b) for a in variable1.domain() for b in variable2.domain() if a < b])
        csp.add_constraint(constraint)

    return csp, variables


def _build_dicts(dimension):
    """
    Builds and caches:
      - sat_dict:  {perm: True} for all n! permutations
      - pos_sup:   {(position, val): [perms with val at position]}

    pos_sup serves double duty:
      - For empty constraints: sup_tuples remaps (var, val) -> pos_sup[(j, val)]
      - For pre-assigned constraints: pos_sup[(j, val)] is already the
        filtered list of perms — no need to scan all n! permutations.
    """
    cache_key = f'dicts_{dimension}'
    if cache_key in PERM_CACHE:
        return PERM_CACHE[cache_key]

    all_perms = list(permutations(range(1, dimension + 1)))
    PERM_CACHE[dimension] = all_perms

    sat_dict = {p: True for p in all_perms}

    pos_sup = {}
    for p in all_perms:
        for idx, val in enumerate(p):
            key = (idx, val)
            if key not in pos_sup:
                pos_sup[key] = []
            pos_sup[key].append(p)

    PERM_CACHE[cache_key] = (sat_dict, pos_sup)
    return sat_dict, pos_sup


def _set_constraint_dicts(constraint, scope, dimension, sat_dict, pos_sup):
    """
    Assigns sat_tuples and sup_tuples directly to a constraint, bypassing
    add_satisfying_tuples entirely.

    - Empty scope (all domains full): O(n!) sat copy + O(n^2) sup remap
    - Pre-assigned scope: O(k) sat build using pos_sup intersection + O(n^2) sup remap
      where k = number of valid tuples (n-m)! for m pre-assigned cells
    """
    domains = [set(v.domain()) for v in scope]

    if all(len(d) == dimension for d in domains):
        # Fast path: all cells empty — copy prebuilt sat, remap sup by position
        constraint.sat_tuples = sat_dict.copy()
        constraint.sup_tuples = {
            (var, val): pos_sup[(j, val)]
            for j, var in enumerate(scope)
            for val in range(1, dimension + 1)
        }
    else:
        # Pre-assigned path: use pos_sup lists as filtered tuples directly
        # pos_sup[(j, val)] is exactly the set of perms with val at position j
        # Intersecting these for all restricted positions gives the filtered list
        restricted = [
            (i, next(iter(domains[i])))
            for i in range(dimension)
            if len(domains[i]) == 1
        ]
        # Start from the smallest pos_sup list (first restricted position)
        filtered = pos_sup[(restricted[0][0], restricted[0][1])]
        for i, val in restricted[1:]:
            s = set(map(id, pos_sup[(i, val)]))
            filtered = [p for p in filtered if id(p) in s]

        constraint.sat_tuples = {p: True for p in filtered}
        # sup_tuples: use full pos_sup lists (superset) — has_support() handles
        # validity checks at search time via cur_domain checks
        constraint.sup_tuples = {
            (var, val): pos_sup[(j, val)]
            for j, var in enumerate(scope)
            for val in range(1, dimension + 1)
        }


def futoshiki_csp_model_2(grid: list[list[Any]]) -> tuple['CSP', list[list['Variable']]]:
    """
    Return a tuple consisting of the constraint satisfaction problem constructed
    according to the input Futoshiki puzzle grid, and a list of lists of Variable
    objects that represents the matrix of values corresponding to the input grid
    indexed from (0, 0) to (n-1, n-1).

    Constraints for model 2 are built using n-ary all-different constraints
    for both rows and columns. That is, there are 2*n + k total constraints:
    n all-different constraints for rows, n all-different constraints for columns,
    and k binary inequality constraints for the inequalities on the board.

    :param grid: a list of lists of objects representing the Futoshiki grid, e.g.
                    grid = [[0,>,0,.,2], [0,.,0,.,0], [0,.,0,<,0]]
    """
    dimension = len(grid)
    variables = []
    inequalities = []
    for row in range(dimension):
        row_variables = []
        for col in range(dimension):
            cell = grid[row][col*2]
            if cell == 0:
                variable = Variable(f"V{row}{col}", list(range(1, dimension + 1)))
            else:
                variable = Variable(f"V{row}{col}", [cell])
            row_variables.append(variable)

            if col < dimension - 1:
                token = grid[row][col*2 + 1]
                if token != '.':
                    inequalities.append((token, row, col))
        variables.append(row_variables)

    csp = CSP("Futoshiki")
    for row in range(dimension):
        for col in range(dimension):
            csp.add_var(variables[row][col])

    # Build sat_dict and pos_sup once for this dimension
    sat_dict, pos_sup = _build_dicts(dimension)

    # every row has to have different values
    for row in range(dimension):
        scope = variables[row]
        constraint = Constraint(f"row{row}", scope)
        _set_constraint_dicts(constraint, scope, dimension, sat_dict, pos_sup)
        csp.add_constraint(constraint)

    # every column has to have different values
    for col in range(dimension):
        scope = [variables[row][col] for row in range(dimension)]
        constraint = Constraint(f"col{col}", scope)
        _set_constraint_dicts(constraint, scope, dimension, sat_dict, pos_sup)
        csp.add_constraint(constraint)

    # add inequality constraints
    for token, row, col in inequalities:
        variable1 = variables[row][col]
        variable2 = variables[row][col + 1]
        constraint = Constraint(f"ineq{row}{col}", [variable1, variable2])
        if token == '>':
            constraint.add_satisfying_tuples([(a, b) for a in variable1.domain() for b in variable2.domain() if a > b])
        elif token == '<':
            constraint.add_satisfying_tuples([(a, b) for a in variable1.domain() for b in variable2.domain() if a < b])
        csp.add_constraint(constraint)

    return csp, variables