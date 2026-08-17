import itertools
import time

from src import (
    CSP,
    Variable,
    Constraint,
    BacktrackingSearch,
)

from test_utils import TestOutput, set_timeout, reset_timeout

try:
    import propagators as student_propagators
    import futoshiki_csp as student_models
except ImportError:
    pass


# Global timeout constant
TIMEOUT = 60

#######################################
# EXAMPLE CSP CONSTRUCTIONS
#######################################
def queens_check(qi, qj, i, j):
    return i != j and abs(i - j) != abs(qi - qj)


def n_queens(n):
    dom = list(range(1, n + 1))
    vars_ = [Variable(f"Q{i}", dom) for i in dom]
    cons = []
    for qi in range(n):
        for qj in range(qi + 1, n):
            c_name = f"C(Q{qi + 1},Q{qj + 1})"
            c = Constraint(c_name, [vars_[qi], vars_[qj]])
            sat_tuples = []
            for t in itertools.product(dom, repeat=2):
                if queens_check(qi, qj, t[0], t[1]):
                    sat_tuples.append(t)
            c.add_satisfying_tuples(sat_tuples)
            cons.append(c)
    csp = CSP(f"{n}-Queens", vars_)
    for c_ in cons:
        csp.add_constraint(c_)
    return csp


def w_eq_sum_x_y_z(values):
    w, x, y, z = values
    return w == (x + y + z)


def even_odd_csp():
    dom = (1, 2, 3, 4)
    vars = []
    vars.append(Variable('X', list(dom)))
    vars.append(Variable('Y', list(dom)))
    con1 = Constraint("X+Y odd", [vars[0], vars[1]])
    sat_tuples = []
    for t in itertools.product(dom, dom):
        if (t[0] + t[1]) % 2 == 1:
            sat_tuples.append(t)
    con1.add_satisfying_tuples(sat_tuples)
    csp = CSP("X + Y odd", vars)
    csp.add_constraint(con1)
    return csp


def three_var_csp():
    dom = (1, 2, 3, 4)
    vars = []
    vars.append(Variable('W', list(dom)))
    vars.append(Variable('X', list(dom)))
    vars.append(Variable('Y', list(dom)))
    vars.append(Variable('Z', list(dom)))
    sat_tuples = []
    con1 = Constraint("W + X < Y", [vars[0], vars[1], vars[2]])
    for t in itertools.product(dom, repeat=3):
        if t[0] + t[1] < t[2]:
            sat_tuples.append(t)
    con1.add_satisfying_tuples(sat_tuples)
    sat_tuples = []
    con2 = Constraint("X + Y < Z", [vars[1], vars[2], vars[3]])
    for t in itertools.product(dom, repeat=3):
        if t[0] + t[1] < t[2]:
            sat_tuples.append(t)
    con2.add_satisfying_tuples(sat_tuples)
    csp = CSP("Tiny comparator", vars)
    csp.add_constraint(con1)
    csp.add_constraint(con2)
    return csp


def three_var_csp2():
    dom = (1, 2, 3, 4)
    vars = []
    vars.append(Variable('W', list(dom)))
    vars.append(Variable('X', list(dom)))
    vars.append(Variable('Y', list(dom)))
    vars.append(Variable('Z', list(dom)))
    sat_tuples = []
    con1 = Constraint("W < X", [vars[0], vars[1]])
    for t in itertools.product(dom, repeat=2):
        if t[0] < t[1]:
            sat_tuples.append(t)
    con1.add_satisfying_tuples(sat_tuples)
    sat_tuples = []
    con2 = Constraint("W + X + Y < Z", [vars[0], vars[1], vars[2], vars[3]])
    for t in itertools.product(dom, repeat=4):
        if t[0] + t[1] + t[2] < t[3]:
            sat_tuples.append(t)
    con2.add_satisfying_tuples(sat_tuples)
    csp = CSP("Tiny comparator2", vars)
    csp.add_constraint(con1)
    csp.add_constraint(con2)
    return csp


def tiny_adder_csp():
    dom = (1, 2, 3, 4)
    vars = []
    vars.append(Variable('X', list(dom)))
    vars.append(Variable('Y', list(dom)))
    vars.append(Variable('Z', list(dom)))
    con1 = Constraint("X + Y = Z", [vars[0], vars[1], vars[2]])
    con2 = Constraint("X > Y", [vars[0], vars[1]])
    sat1 = []
    for t in itertools.product(dom, repeat=3):
        if t[0] + t[1] == t[2]:
            sat1.append(t)
    con1.add_satisfying_tuples(sat1)
    sat2 = []
    for t in itertools.product(dom, dom):
        if t[0] > t[1]:
            sat2.append(t)
    con2.add_satisfying_tuples(sat2)
    csp = CSP("Tiny adder", vars)
    csp.add_constraint(con1)
    csp.add_constraint(con2)
    return csp


#######################################
# TEST FUNCTIONS
#######################################

def test_simple_fc(stu_propagators, test_name) -> TestOutput:
    max_score = 1
    score = 0
    output = ""
    errors = ""
    try:
        csp = n_queens(8)
        curr_vars = csp.get_all_vars()
        curr_vars[0].assign(1)
        stu_propagators.prop_FC(csp, newVar=curr_vars[0])
        expected = [
            [1],
            [3, 4, 5, 6, 7, 8],
            [2, 4, 5, 6, 7, 8],
            [2, 3, 5, 6, 7, 8],
            [2, 3, 4, 6, 7, 8],
            [2, 3, 4, 5, 7, 8],
            [2, 3, 4, 5, 6, 8],
            [2, 3, 4, 5, 6, 7]
        ]
        var_domain = [v.cur_domain() for v in curr_vars]
        if var_domain == expected:
            score = max_score
            output = "FC propagation successful"
        else:
            errors = "Failed simple FC test: variable domains differ"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Tests FC after the first queen is placed in position 1.",
                      output=output, errors=errors)


def test_simple_gac(stu_propagators, test_name) -> TestOutput:
    max_score = 1
    score = 0
    output = ""
    errors = ""
    try:
        csp = n_queens(8)
        vars_ = csp.get_all_vars()
        vars_[0].assign(1)
        stu_propagators.prop_GAC(csp, newVar=vars_[0])
        expected = [
            [1],
            [3, 4, 5, 6, 7, 8],
            [2, 4, 5, 6, 7, 8],
            [2, 3, 5, 6, 7, 8],
            [2, 3, 4, 6, 7, 8],
            [2, 3, 4, 5, 7, 8],
            [2, 3, 4, 5, 6, 8],
            [2, 3, 4, 5, 6, 7]
        ]
        var_domain = [v.cur_domain() for v in vars_]
        if var_domain == expected:
            score = max_score
            output = "GAC propagation successful"
        else:
            errors = "Failed simple GAC test: variable domains differ"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Tests GAC after the first queen is placed in position 1.",
                      output=output, errors=errors)


def three_queen_gac(stu_propagators, test_name) -> TestOutput:
    max_score = 1
    score = 0
    output = ""
    errors = ""
    try:
        csp = n_queens(8)
        vars_ = csp.get_all_vars()
        vars_[0].assign(4)
        vars_[2].assign(1)
        vars_[7].assign(5)
        stu_propagators.prop_GAC(csp)
        expected = [
            [4], [6, 7, 8], [1], [3, 8],
            [6, 7], [2, 8], [2, 3, 7, 8], [5]
        ]
        var_vals = [v.cur_domain() for v in vars_]
        if var_vals == expected:
            score = max_score
            output = "Three queens GAC propagation successful"
        else:
            errors = "Failed three queens GAC test: domain mismatch"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="A 3-queen scenario that yields different prunings for FC vs GAC.",
                      output=output, errors=errors)


def three_queen_fc(stu_propagators, test_name) -> TestOutput:
    max_score = 1
    score = 0
    output = ""
    errors = ""
    try:
        csp = n_queens(8)
        vars_ = csp.get_all_vars()
        vars_[0].assign(4)
        vars_[2].assign(1)
        vars_[7].assign(5)
        stu_propagators.prop_FC(csp)
        expected = [
            [4], [6, 7, 8], [1], [3, 6, 8],
            [6, 7], [2, 6, 8], [2, 3, 7, 8], [5]
        ]
        var_vals = [v.cur_domain() for v in vars_]
        if var_vals == expected:
            score = max_score
            output = "Three queens FC propagation successful"
        else:
            errors = "Failed three queens FC test: domain mismatch"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Similar 3-queen scenario but checking FC specifically.",
                      output=output, errors=errors)


def test_prop_1(propagator, test_name) -> TestOutput:
    max_score = 1
    score = 0
    output = ""
    errors = ""
    try:
        x = Variable('X', [1, 2, 3])
        y = Variable('Y', [1, 2, 3])
        z = Variable('Z', [1, 2, 3])
        w = Variable('W', [1, 2, 3, 4])
        c1 = Constraint('C1', [x, y, z])
        c1.add_satisfying_tuples([[2, 1, 1], [3, 1, 2], [3, 2, 1]])
        c2 = Constraint('C2', [w, x, y, z])
        var_doms = [v.domain() for v in [w, x, y, z]]
        sat_tuples = []
        for t in itertools.product(*var_doms):
            if w_eq_sum_x_y_z(t):
                sat_tuples.append(t)
        c2.add_satisfying_tuples(sat_tuples)
        simple_csp = CSP("SimpleEqs", [x, y, z, w])
        simple_csp.add_constraint(c1)
        simple_csp.add_constraint(c2)
        btracker = BacktrackingSearch(simple_csp)
        set_timeout(TIMEOUT)
        btracker.search(propagator)
        curr_vars = simple_csp.get_all_vars()
        answer = [[2], [1], [1], [4]]
        var_vals = [v.cur_domain() for v in curr_vars]
        reset_timeout()
        if var_vals != answer:
            errors = f"Failed while testing a propagator ({test_name}): variable domains don't match expected results"
        else:
            score = max_score
            output = f"Test {test_name} passed successfully"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description=f"Tests a propagator ({test_name}) on a simple CSP.",
                      output=output, errors=errors)


def test_prop_2(propagator, test_name) -> TestOutput:
    max_score = 1
    score = 0
    output = ""
    errors = ""
    try:
        x = Variable('X', [1, 2, 3])
        y = Variable('Y', [1, 2, 3])
        z = Variable('Z', [1, 2, 3])
        c1 = Constraint('C1', [x, y, z])
        c1.add_satisfying_tuples([[2, 1, 1], [3, 1, 2], [3, 2, 1]])
        c2 = Constraint('C2', [x, y])
        c2.add_satisfying_tuples([[1, 2], [2, 1], [2, 3], [3, 2]])
        c3 = Constraint('C3', [y, z])
        c3.add_satisfying_tuples([[1, 2], [1, 3], [2, 1], [2, 3], [3, 1], [3, 2]])
        simple_csp = CSP("ParityEqs", [x, y, z])
        simple_csp.add_constraint(c1)
        simple_csp.add_constraint(c2)
        simple_csp.add_constraint(c3)
        btracker = BacktrackingSearch(simple_csp)
        set_timeout(TIMEOUT)
        btracker.search(propagator)
        reset_timeout()
        curr_vars = simple_csp.get_all_vars()
        answer = [[3], [2], [1]]
        var_vals = [v.cur_domain() for v in curr_vars]
        if var_vals != answer:
            errors = f"Failed while testing a propagator ({test_name}): variable domains don't match expected results"
        else:
            score = max_score
            output = f"Test {test_name} passed successfully"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description=f"Tests a propagator ({test_name}) on a CSP with parity constraints.",
                      output=output, errors=errors)


def test_prop_3(propagator, test_name) -> TestOutput:
    max_score = 1
    score = 0
    output = ""
    errors = ""
    try:
        x = Variable('X', [1, 2, 3])
        y = Variable('Y', [1, 2, 3])
        z = Variable('Z', [1, 2, 3])
        c1 = Constraint('C1', [x, y, z])
        c1.add_satisfying_tuples([[2, 1, 1], [3, 1, 2], [3, 2, 1]])
        c2 = Constraint('C2', [y, z])
        c2.add_satisfying_tuples([[1, 1], [1, 3], [2, 2], [3, 1], [3, 3]])
        c3 = Constraint('C3', [x, y])
        c3.add_satisfying_tuples([[1, 1], [1, 3], [2, 2], [3, 1], [3, 3]])
        simple_csp = CSP("ParityEqs", [x, y, z])
        simple_csp.add_constraint(c1)
        simple_csp.add_constraint(c2)
        simple_csp.add_constraint(c3)
        btracker = BacktrackingSearch(simple_csp)
        set_timeout(TIMEOUT)
        btracker.search(propagator)
        reset_timeout()
        curr_vars = simple_csp.get_all_vars()
        answer = [[1, 2, 3], [1, 2, 3], [1, 2, 3]]
        var_vals = [v.cur_domain() for v in curr_vars]
        if var_vals != answer:
            errors = f"Failed while testing a propagator ({test_name}): variable domains don't match expected results"
        else:
            score = max_score
            output = f"Test {test_name} passed successfully"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description=f"Tests a propagator ({test_name}) on a CSP with parity constraints.",
                      output=output, errors=errors)


def test_tiny_adder_fc(stu_propagators, test_name) -> TestOutput:
    max_score = 5
    score = 0
    output = ""
    errors = ""
    try:
        csp = tiny_adder_csp()
        curr_vars = csp.get_all_vars()
        curr_vars[0].assign(3)
        set_timeout(TIMEOUT)
        stu_propagators.prop_FC(csp, newVar=curr_vars[0])
        reset_timeout()
        var_domain = [x.cur_domain() for x in curr_vars]
        answer = [[3], [1, 2], [1, 2, 3, 4]]
        if var_domain == answer:
            score = max_score
            output = "Tiny adder FC test passed"
        else:
            errors = "Failed small FC test: variable domains don't match expected results"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Tests FC on a tiny adder CSP.",
                      output=output, errors=errors)


def test_tiny_adder_gac(stu_propagators, test_name) -> TestOutput:
    max_score = 5
    score = 0
    output = ""
    errors = ""
    try:
        csp = tiny_adder_csp()
        curr_vars = csp.get_all_vars()
        curr_vars[0].assign(3)
        set_timeout(TIMEOUT)
        stu_propagators.prop_GAC(csp, newVar=curr_vars[0])
        reset_timeout()
        var_domain = [x.cur_domain() for x in curr_vars]
        answer = [[3], [1], [4]]
        if var_domain == answer:
            score = max_score
            output = "Tiny adder GAC test passed"
        else:
            errors = "Failed small GAC test: variable domains don't match expected results"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Tests GAC on a tiny adder CSP.",
                      output=output, errors=errors)


def test_no_pruning_fc(stu_propagators, test_name) -> TestOutput:
    max_score = 3
    score = 0
    output = ""
    errors = ""
    try:
        csp = three_var_csp()
        curr_vars = csp.get_all_vars()
        curr_vars[1].assign(3)
        set_timeout(TIMEOUT)
        stu_propagators.prop_FC(csp, newVar=curr_vars[1])
        reset_timeout()
        var_domain = [x.cur_domain() for x in curr_vars]
        answer = [[1, 2, 3, 4], [3], [1, 2, 3, 4], [1, 2, 3, 4]]
        if var_domain == answer:
            score = max_score
            output = "FC test with no pruning passed"
        else:
            errors = "Failed FC test that should have resulted in no pruning"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Tests FC on a CSP that should result in no pruning.",
                      output=output, errors=errors)


def test_no_pruning2_fc(stu_propagators, test_name) -> TestOutput:
    max_score = 3
    score = 0
    output = ""
    errors = ""
    try:
        csp = three_var_csp2()
        curr_vars = csp.get_all_vars()
        curr_vars[1].assign(1)
        curr_vars[2].assign(1)
        set_timeout(TIMEOUT)
        stu_propagators.prop_FC(csp, newVar=curr_vars[2])
        reset_timeout()
        var_domain = [x.cur_domain() for x in curr_vars]
        answer = [[1, 2, 3, 4], [1], [1], [1, 2, 3, 4]]
        if var_domain == answer:
            score = max_score
            output = "FC test with no pruning (variant 2) passed"
        else:
            errors = "Failed FC test that should have resulted in no pruning"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Tests FC on a CSP that should result in no pruning (variant 2).",
                      output=output, errors=errors)


def test_no_pruning_gac(stu_propagators, test_name) -> TestOutput:
    max_score = 6
    score = 0
    output = ""
    errors = ""
    try:
        csp = even_odd_csp()
        set_timeout(TIMEOUT)
        stu_propagators.prop_GAC(csp)
        reset_timeout()
        curr_vars = csp.get_all_vars()
        var_domain = [x.cur_domain() for x in curr_vars]
        answer = [[1, 2, 3, 4], [1, 2, 3, 4]]
        if var_domain == answer:
            score = max_score
            output = "GAC test with no pruning passed"
        else:
            errors = "Failed GAC test that should have resulted in no pruning"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Tests GAC on a CSP that should result in no pruning.",
                      output=output, errors=errors)


def test_dwo_gac(stu_propagators, test_name) -> TestOutput:
    max_score = 5
    score = 0
    output = ""
    errors = ""
    try:
        csp = n_queens(6)
        curr_vars = csp.get_all_vars()
        curr_vars[0].assign(2)
        set_timeout(TIMEOUT)
        pruned = stu_propagators.prop_GAC(csp, newVar=curr_vars[0])
        if not pruned[0]:
            errors = "Failed a GAC test: returned DWO too early"
        else:
            curr_vars[1].assign(5)
            pruned = stu_propagators.prop_GAC(csp, newVar=curr_vars[1])
            reset_timeout()
            if pruned[0]:
                errors = "Failed a GAC test: should have resulted in a DWO"
            else:
                score = max_score
                output = "GAC DWO test passed"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Tests GAC on a CSP that should result in a domain wipeout.",
                      output=output, errors=errors)


def test_dwo_fc(stu_propagators, test_name) -> TestOutput:
    max_score = 5
    score = 0
    output = ""
    errors = ""
    try:
        csp = n_queens(6)
        curr_vars = csp.get_all_vars()
        curr_vars[0].assign(2)
        set_timeout(TIMEOUT)
        pruned = stu_propagators.prop_FC(csp, newVar=curr_vars[0])
        if not pruned[0]:
            errors = "Failed a FC test: returned DWO too early"
        else:
            curr_vars[1].assign(5)
            pruned = stu_propagators.prop_FC(csp, newVar=curr_vars[1])
            if not pruned[0]:
                errors = "Failed a FC test: returned DWO too early"
            else:
                curr_vars[4].assign(1)
                pruned = stu_propagators.prop_FC(csp, newVar=curr_vars[4])
                reset_timeout()
                if pruned[0]:
                    errors = "Failed a FC test: should have resulted in a DWO"
                else:
                    score = max_score
                    output = "FC DWO test passed"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Tests FC on a CSP that should result in a domain wipeout.",
                      output=output, errors=errors)


def test_futoshiki_model_1(stu_models, test_name) -> TestOutput:
    max_score = 1
    score = 0
    output = ""
    errors = ""
    try:
        board = [[3, '.', 0, '.', 0, '<', 0],
                 [0, '.', 0, '.', 0, '.', 0],
                 [0, '.', 0, '<', 0, '.', 0],
                 [0, '.', 0, '>', 0, '.', 1]]
        answer = [[3], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4],
                  [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4],
                  [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4],
                  [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1]]
        set_timeout(TIMEOUT)
        csp, var_array = stu_models.futoshiki_csp_model_1(board)
        reset_timeout()
        if csp is None or len(var_array) == 0:
            errors = "Failed to import a board into model 1"
        else:
            lister = [var_array[i][j].cur_domain() for i in range(4) for j in range(4)]
            if lister != answer:
                errors = "Failed to import a board into model 1: initial domains don't match"
            else:
                score = max_score
                output = "Futoshiki model 1 board import successful"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Tests importing a board into Futoshiki model 1.",
                      output=output, errors=errors)


def test_futoshiki_model_2(stu_models, test_name) -> TestOutput:
    max_score = 1
    score = 0
    output = ""
    errors = ""
    try:
        board = [[3, '.', 0, '.', 0, '<', 0],
                 [0, '.', 0, '.', 0, '.', 0],
                 [0, '.', 0, '<', 0, '.', 0],
                 [0, '.', 0, '>', 0, '.', 1]]
        answer = [[3], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4],
                  [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4],
                  [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4],
                  [1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4], [1]]
        set_timeout(TIMEOUT)
        csp, var_array = stu_models.futoshiki_csp_model_2(board)
        reset_timeout()
        if csp is None:
            errors = "Failed to construct CSP"
        else:
            lister = [var_array[i][j].cur_domain() for i in range(4) for j in range(4)]
            if lister != answer:
                errors = "Failed to import a board into model 2: initial domains don't match"
            else:
                score = max_score
                output = "Futoshiki model 2 board import successful"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Tests importing a board into Futoshiki model 2.",
                      output=output, errors=errors)


def check_model_1_constraints_enum_rewscols(stu_models, test_name) -> TestOutput:
    max_score = 1
    score = 0
    output = ""
    errors = ""
    try:
        board = [[3, '.', 2, '.', 0],
                 [1, '.', 3, '.', 0],
                 [0, '.', 0, '.', 0]]
        set_timeout(TIMEOUT)
        csp, var_array = stu_models.futoshiki_csp_model_1(board)
        reset_timeout()
        if csp is None:
            errors = "Failed to construct Model 1"
        else:
            for cons in csp.get_all_cons():
                all_vars = cons.get_scope()
                taken = []
                domain_list = []
                should_pass = []
                should_fail = []
                for va in all_vars:
                    domain_list.append(va.cur_domain())
                    if len(va.cur_domain()) == 1:
                        taken.append(va.cur_domain()[0])
                for i in range(len(all_vars)):
                    va = all_vars[i]
                    domain = domain_list[i]
                    if len(domain) == 1:
                        should_pass.append(domain[0])
                        should_fail.append(domain[0])
                    else:
                        for v in range(1, 4):
                            if v in domain and v in taken:
                                should_fail.append(v)
                                break
                        for v in range(1, 4):
                            if v in domain and v not in taken:
                                should_pass.append(v)
                                taken.append(v)
                                break
                if cons.check(should_fail) != cons.check(should_pass):
                    if cons.check(should_fail) or not cons.check(should_pass):
                        if not cons.check(should_fail):
                            errors = f"Failed constraint test in model 1: {cons} should be falsified by {should_fail}"
                            break
                        if cons.check(should_pass):
                            errors = f"Failed constraint test in model 1: {cons} should be satisfied by {should_fail}"
                            break
            else:
                score = max_score
                output = "Model 1 constraints enum rewscols check passed"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Checks that model 1 constraints pass when all different, and fail when not all different.",
                      output=output, errors=errors)


def check_model_2_constraints_enum_rewscols(stu_models, test_name) -> TestOutput:
    max_score = 1
    score = 0
    output = ""
    errors = ""
    try:
        board = [[3, '.', 2, '.', 0],
                 [1, '.', 3, '.', 0],
                 [0, '.', 0, '.', 0]]
        csp, var_array = stu_models.futoshiki_csp_model_2(board)
        if csp is None:
            errors = "Tried to make CSP, got nothing"
        else:
            for cons in csp.get_all_cons():
                all_vars = cons.get_scope()
                taken = []
                domain_list = []
                should_pass = []
                should_fail = []
                for va in all_vars:
                    domain_list.append(va.cur_domain())
                    if len(va.cur_domain()) == 1:
                        taken.append(va.cur_domain()[0])
                for i in range(len(all_vars)):
                    va = all_vars[i]
                    domain = domain_list[i]
                    if len(domain) == 1:
                        should_pass.append(domain[0])
                        should_fail.append(domain[0])
                    else:
                        for v in range(1, 4):
                            if v in domain and v in taken:
                                should_fail.append(v)
                                break
                        for v in range(1, 4):
                            if v in domain and v not in taken:
                                should_pass.append(v)
                                taken.append(v)
                                break
                if cons.check(should_fail) != cons.check(should_pass):
                    if cons.check(should_fail) or not cons.check(should_pass):
                        if not cons.check(should_fail):
                            errors = f"Failed constraint test in model 2: {cons} should be falsified by {should_fail}"
                            break
                        if cons.check(should_pass):
                            errors = f"Failed constraint test in model 2: {cons} should be satisfied by {should_fail}"
                            break
            else:
                score = max_score
                output = "Model 2 constraints enum rewscols check passed"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Checks that model 2 constraints pass when all different, and fail when not all different.",
                      output=output, errors=errors)


def check_binary_constraint_model_1(stu_model, test_name) -> TestOutput:
    max_score = 2
    score = 0
    output = ""
    errors = ""
    try:
        board = [[0, '.', 2, '.', 0, '.', 0, '.', 0],
                 [0, '>', 3, '.', 0, '.', 0, '<', 0],
                 [2, '.', 0, '.', 0, '.', 0, '<', 0],
                 [0, '.', 0, '.', 0, '<', 0, '.', 0],
                 [0, '>', 0, '.', 0, '.', 0, '.', 5]]
        set_timeout(TIMEOUT)
        csp, var_array = stu_model.futoshiki_csp_model_1(board)
        reset_timeout()
        if csp is None:
            errors = "Tried to construct CSP, got nothing"
        else:
            score = max_score
            output = "Binary constraint model 1 check passed"
            for con in csp.get_all_cons():
                if len(con.get_scope()) != 2:
                    score = 0
                    errors = f"Model 1 specifies ONLY binary constraints. Found a constraint of length {len(con.get_scope())}"
                    break
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Checks that students followed the handout and actually only have constraints over two variables for model 1.",
                      output=output, errors=errors)


def check_nary_constraint_model_2(stu_model, test_name) -> TestOutput:
    max_score = 2
    score = 2
    output = ""
    errors = ""
    try:
        board = [[0, '.', 2, '.', 0, '.', 0, '.', 0],
                 [0, '>', 3, '.', 0, '.', 0, '<', 0],
                 [2, '.', 0, '.', 0, '.', 0, '<', 0],
                 [0, '.', 0, '.', 0, '<', 0, '.', 0],
                 [0, '>', 0, '.', 0, '.', 0, '.', 5]]
        csp, var_array = stu_model.futoshiki_csp_model_2(board)
        if csp is None:
            score = 0
            errors = "Tried to make CSP, got nothing"
        else:
            saw_nary = False
            for con in csp.get_all_cons():
                all_vars = con.get_scope()
                if len(all_vars) == 5:
                    saw_nary = True
                elif len(all_vars) != 2:
                    score = 0
                    errors = f"Model 2 specifies ONLY binary and nary constraints. Found a constraint of length {len(all_vars)}"
                    break
            if saw_nary:
                score = max_score
                output = "Nary constraint model 2 check passed"
            else:
                score = 0
                errors = "Model 2 specifies that nary constraints must be used for the row/col constraints. Only binary constraints were used."
    except Exception as ex:
        score = 0
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Checks that model 2 uses n-ary constraints for rows and columns.",
                      output=output, errors=errors)


def check_out_of_domain_tuple(prop, test_name) -> TestOutput:
    max_score = 4
    score = 0
    output = ""
    errors = ""
    try:
        board = [[0, '.', 2, '.', 0, '.', 0, '.', 0],
                 [0, '>', 3, '.', 0, '.', 0, '<', 0],
                 [2, '.', 0, '.', 0, '.', 0, '<', 0],
                 [0, '.', 0, '.', 0, '<', 0, '.', 0],
                 [0, '>', 0, '.', 0, '.', 0, '.', 5]]
        csp, var_array = prop(board)
        if csp is None:
            errors = "Tried to make CSP, got nothing"
        else:
            var_01 = var_array[0][1]
            all_cons = csp.get_cons_with_var(var_01)
            seen_var01 = False
            for con in all_cons:
                curr_scope = con.get_scope()
                if var_01 in curr_scope:
                    seen_var01 = True
                    if not con.has_support(var_01, 2):
                        errors = f"Failed while testing propagator ({test_name}): a constraint fails on a valid input"
                        break
                    elif (con.has_support(var_01, 1) or con.has_support(var_01, 3)
                          or con.has_support(var_01, 4) or con.has_support(var_01, 5)):
                        errors = f"Failed while testing propagator ({test_name}): a constraint contains an out-of-domain value"
                        break
            if seen_var01 and not errors:
                score = max_score
                output = "Out of domain tuple check passed"
            elif not seen_var01:
                errors = f"Failed while testing propagator ({test_name}): found no constraint containing a specific variable"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Checks that constraints do not contain out-of-domain values.",
                      output=output, errors=errors)


def test_ord_mrv(stu_propagators, test_name) -> TestOutput:
    max_score = 5
    score = 0
    output = ""
    errors = ""
    details = ""
    try:
        # Test 1
        a = Variable('A', [1]); b = Variable('B', [1]); c = Variable('C', [1])
        d = Variable('D', [1]); e = Variable('E', [1])
        simple_csp = CSP("Simple", [a, b, c, d, e])
        for i, var in enumerate(simple_csp.variables):
            var.add_domain_values(range(i))
        var = stu_propagators.ord_mrv(simple_csp)
        if var and var.name == simple_csp.variables[0].name:
            details += "Passed 1st Ord MRV Test. "; score += 1
        else:
            details += "Failed 1st Ord MRV Test. "

        # Test 2
        a = Variable('A', [1,2,3,4,5]); b = Variable('B', [1,2,3,4])
        c = Variable('C', [1,2]); d = Variable('D', [1,2,3]); e = Variable('E', [1])
        simple_csp = CSP("Simple", [a, b, c, d, e])
        var = stu_propagators.ord_mrv(simple_csp)
        if var and var.name == simple_csp.variables[-1].name:
            details += "Passed 2nd Ord MRV Test. "; score += 1
        else:
            details += "Failed 2nd Ord MRV Test. "

        # Test 3
        a = Variable('A', [1,2,3,4,5]); b = Variable('B', [1])
        c = Variable('C', [1,2]); d = Variable('D', [1,2,3]); e = Variable('E', [1,2,3,4])
        simple_csp = CSP("Simple", [a, b, c, d, e])
        var = stu_propagators.ord_mrv(simple_csp)
        if var and var.name == simple_csp.variables[1].name:
            details += "Passed 3rd Ord MRV Test. "; score += 1
        else:
            details += "Failed 3rd Ord MRV Test. "

        # Test 4
        a = Variable('A', [1,2,3,4,5]); b = Variable('B', [1,2,3,4])
        c = Variable('C', [1]); d = Variable('D', [1,2,3]); e = Variable('E', [1,2,3])
        simple_csp = CSP("Simple", [a, b, c, d, e])
        var = stu_propagators.ord_mrv(simple_csp)
        if var and var.name == simple_csp.variables[2].name:
            details += "Passed 4th Ord MRV Test. "; score += 1
        else:
            details += "Failed 4th Ord MRV Test. "

        # Test 5
        a = Variable('A', [1,2,3,4,5]); b = Variable('B', [1,2,3,4])
        c = Variable('C', [1,2]); d = Variable('D', [1]); e = Variable('E', [1,2])
        simple_csp = CSP("Simple", [a, b, c, d, e])
        var = stu_propagators.ord_mrv(simple_csp)
        if var and var.name == simple_csp.variables[3].name:
            details += "Passed 5th Ord MRV Test. "; score += 1
        else:
            details += "Failed 5th Ord MRV Test. "

        output = f"MRV tests: {details}"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Tests the Minimum Remaining Values (MRV) heuristic.",
                      output=output, errors=errors)


def test_model_2_construction_time(stu_models, test_name) -> TestOutput:
    """Tests that constructing a 9x9 Model 2 CSP takes < 1 second."""
    max_score = 2
    score = 0
    output = ""
    errors = ""
    try:
        n = 9
        board = []
        for i in range(n):
            row = []
            for j in range(n):
                row.append(0)
                if j < n - 1:
                    row.append('.')
            board.append(row)
        start = time.time()
        csp, var_array = stu_models.futoshiki_csp_model_2(board)
        elapsed = time.time() - start
        if elapsed < 1.0:
            score = max_score
            output = f"Model 2 construction time: {elapsed:.4f} seconds (PASS)"
        else:
            errors = f"Model 2 construction too slow: {elapsed:.4f} seconds (>1s)"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Tests that Model 2 builds a 9x9 CSP in under 1 second.",
                      output=output, errors=errors)


def test_model2_construction_time_with_clues(stu_models, test_name) -> TestOutput:
    """Tests that Model 2 builds a 9x9 CSP with pre-assigned cells in under 1 second."""
    max_score = 2
    score = 0
    output = ""
    errors = ""
    try:
        # Diagonal pre-assignments: 1 clue per row, each in a different column
        n = 9
        given = {(r, r): r + 1 for r in range(n)}
        grid = []
        for r in range(n):
            row = []
            for c in range(n):
                row.append(given.get((r, c), 0))
                if c < n - 1:
                    row.append('.')
            grid.append(row)
        start = time.time()
        csp, variables = stu_models.futoshiki_csp_model_2(grid)
        elapsed = time.time() - start
        if elapsed < 1.0:
            score = max_score
            output = f"Model 2 with clues: {elapsed:.4f}s (PASS)"
        else:
            errors = f"Too slow with clues: {elapsed:.4f}s (>1s) — get_sat_tuples may not be filtering correctly"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Tests that Model 2 builds a 9x9 CSP with pre-assigned cells in under 1 second.",
                      output=output, errors=errors)


def test_model2_preassigned_rows(stu_models, test_name) -> TestOutput:
    """Row tuples must respect pre-assigned cell domains."""
    max_score = 2
    score = 0
    output = ""
    errors = ""
    try:
        # V00 pre-assigned to 1 — every row0 tuple must have 1 at position 0
        grid = [[1, '.', 0, '.', 0],
                [0, '.', 0, '.', 0],
                [0, '.', 0, '.', 0]]
        csp, variables = stu_models.futoshiki_csp_model_2(grid)
        row0 = next(c for c in csp.get_all_cons() if c.name == 'row0')
        bad = [t for t in row0.sat_tuples if t[0] != 1]
        if bad:
            errors = f"row0 has {len(bad)} tuples where position 0 != 1, e.g. {bad[0]}"
        else:
            score = max_score
            output = "Row tuples correctly filtered for pre-assigned cells"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Checks that row satisfying tuples respect pre-assigned cell domains.",
                      output=output, errors=errors)


def test_model2_preassigned_cols(stu_models, test_name) -> TestOutput:
    """Column tuples must respect pre-assigned cell domains."""
    max_score = 2
    score = 0
    output = ""
    errors = ""
    try:
        # V00 pre-assigned to 1 — every col0 tuple must have 1 at position 0
        grid = [[1, '.', 0, '.', 0],
                [0, '.', 0, '.', 0],
                [0, '.', 0, '.', 0]]
        csp, variables = stu_models.futoshiki_csp_model_2(grid)
        col0 = next(c for c in csp.get_all_cons() if c.name == 'col0')
        bad = [t for t in col0.sat_tuples if t[0] != 1]
        if bad:
            errors = f"col0 has {len(bad)} tuples where position 0 != 1, e.g. {bad[0]}"
        else:
            score = max_score
            output = "Col tuples correctly filtered for pre-assigned cells"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Checks that column satisfying tuples respect pre-assigned cell domains.",
                      output=output, errors=errors)


def test_model2_9x9_preassigned_tuples_correct(stu_models, test_name) -> TestOutput:
    """On 9x9 with pre-assigned cells, row/col tuples must respect those assignments."""
    max_score = 2
    score = 0
    output = ""
    errors = ""
    try:
        given = {(0,0):1, (1,1):2, (2,2):3, (3,3):4, (4,4):5}
        n = 9
        grid = []
        for r in range(n):
            row = []
            for c in range(n):
                row.append(given.get((r, c), 0))
                if c < n - 1:
                    row.append('.')
            grid.append(row)
        csp, variables = stu_models.futoshiki_csp_model_2(grid)
        found_error = False
        for r, c in given:
            expected_val = given[(r, c)]
            row_con = next((con for con in csp.get_all_cons() if con.name == f'row{r}'), None)
            if row_con:
                bad = [t for t in row_con.sat_tuples if t[c] != expected_val]
                if bad:
                    errors = f"row{r}: {len(bad)} tuples where position {c} != {expected_val}"
                    found_error = True
                    break
            col_con = next((con for con in csp.get_all_cons() if con.name == f'col{c}'), None)
            if col_con:
                bad = [t for t in col_con.sat_tuples if t[r] != expected_val]
                if bad:
                    errors = f"col{c}: {len(bad)} tuples where position {r} != {expected_val}"
                    found_error = True
                    break
        if not found_error:
            score = max_score
            output = "All row/col tuples correctly filtered for pre-assigned cells on 9x9"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Checks that 9x9 row/col tuples respect pre-assigned cell values.",
                      output=output, errors=errors)


def test_model2_9x9_tuple_count_with_clues(stu_models, test_name) -> TestOutput:
    """With pre-assigned cells, tuple count should be less than 9! per affected constraint."""
    max_score = 1
    score = 0
    output = ""
    errors = ""
    try:
        n = 9
        nine_factorial = 362880
        # Each row has its first column pre-assigned to a unique value
        grid = []
        for r in range(n):
            row = []
            for c in range(n):
                row.append(r + 1 if c == 0 else 0)
                if c < n - 1:
                    row.append('.')
            grid.append(row)
        csp, _ = stu_models.futoshiki_csp_model_2(grid)
        for con in csp.get_all_cons():
            if 'ineq' not in con.name:
                count = len(con.sat_tuples)
                if count == nine_factorial:
                    errors = (f"{con.name} has all 9! tuples despite pre-assigned cells "
                              f"— get_sat_tuples is not filtering")
                    break
        if not errors:
            score = max_score
            output = "Tuple counts correctly reduced by pre-assigned cells"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Checks that tuple counts are reduced when pre-assigned cells exist.",
                      output=output, errors=errors)


def test_model2_constraint_count(stu_models, test_name) -> TestOutput:
    """Model 2 must have exactly 2n + k constraints."""
    max_score = 1
    score = 0
    output = ""
    errors = ""
    try:
        # 3x3 board with 2 inequalities -> 2*3 + 2 = 8 constraints
        grid = [[0, '<', 0, '.', 0],
                [0, '.', 0, '>', 0],
                [0, '.', 0, '.', 0]]
        csp, _ = stu_models.futoshiki_csp_model_2(grid)
        n, k = 3, 2
        expected = 2 * n + k
        actual = len(csp.get_all_cons())
        if actual != expected:
            errors = f"Expected {expected} constraints (2n+k = 2*3+2), got {actual}"
        else:
            score = max_score
            output = f"Correct: {actual} constraints"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Checks that Model 2 has exactly 2n + k constraints.",
                      output=output, errors=errors)


def test_model1_constraint_count(stu_models, test_name) -> TestOutput:
    """Model 1 must have exactly 2 * n * C(n,2) binary neq constraints (no inequalities)."""
    max_score = 1
    score = 0
    output = ""
    errors = ""
    try:
        # 4x4 with no inequalities -> 2 * 4 * C(4,2) = 2 * 4 * 6 = 48
        grid = [[0, '.', 0, '.', 0, '.', 0],
                [0, '.', 0, '.', 0, '.', 0],
                [0, '.', 0, '.', 0, '.', 0],
                [0, '.', 0, '.', 0, '.', 0]]
        csp, _ = stu_models.futoshiki_csp_model_1(grid)
        n = 4
        expected = 2 * n * (n * (n - 1) // 2)
        actual = len(csp.get_all_cons())
        if actual != expected:
            errors = f"Expected {expected} constraints (2*n*C(n,2) = 48 for n=4), got {actual}"
        else:
            score = max_score
            output = f"Correct: {actual} constraints"
    except Exception as ex:
        errors = f"Exception encountered: {ex}"
    return TestOutput(name=test_name, score=score, max_score=max_score,
                      description="Checks that Model 1 has the correct number of binary constraints.",
                      output=output, errors=errors)


#######################################
# TEST LIST
#######################################
futoshiki_tests = [
    # FC
    (test_simple_fc,        student_propagators,            "test_simple_fc",               "FC"),
    (three_queen_fc,        student_propagators,            "three_queen_fc",               "FC"),
    (test_prop_1,           student_propagators.prop_FC,    "test_prop_1_FC",               "FC"),
    (test_prop_2,           student_propagators.prop_FC,    "test_prop_2_FC",               "FC"),
    (test_prop_3,           student_propagators.prop_FC,    "test_prop_3_FC",               "FC"),
    (test_tiny_adder_fc,    student_propagators,            "test_tiny_adder_fc",           "FC"),
    (test_no_pruning_fc,    student_propagators,            "test_no_pruning_fc",           "FC"),
    (test_no_pruning2_fc,   student_propagators,            "test_no_pruning2_fc",          "FC"),
    (test_dwo_fc,           student_propagators,            "test_dwo_fc",                  "FC"),

    # GAC
    (test_simple_gac,       student_propagators,            "test_simple_gac",              "GAC"),
    (three_queen_gac,       student_propagators,            "three_queen_gac",              "GAC"),
    (test_prop_1,           student_propagators.prop_GAC,   "test_prop_1_GAC",              "GAC"),
    (test_prop_2,           student_propagators.prop_GAC,   "test_prop_2_GAC",              "GAC"),
    (test_prop_3,           student_propagators.prop_GAC,   "test_prop_3_GAC",              "GAC"),
    (test_tiny_adder_gac,   student_propagators,            "test_tiny_adder_gac",          "GAC"),
    (test_no_pruning_gac,   student_propagators,            "test_no_pruning_gac",          "GAC"),
    (test_dwo_gac,          student_propagators,            "test_dwo_gac",                 "GAC"),

    # Model 1
    (test_futoshiki_model_1,                student_models, "test_futoshiki_model_1",               "Model 1"),
    (check_model_1_constraints_enum_rewscols, student_models, "check_model_1_constraints_enum_rewscols", "Model 1"),
    (check_binary_constraint_model_1,       student_models, "check_binary_constraint_model_1",      "Model 1"),
    (test_model1_constraint_count,          student_models, "test_model1_constraint_count",          "Model 1"),

    # Model 2
    (test_futoshiki_model_2,                student_models, "test_futoshiki_model_2",               "Model 2"),
    (check_model_2_constraints_enum_rewscols, student_models, "check_model_2_constraints_enum_rewscols", "Model 2"),
    (check_nary_constraint_model_2,         student_models, "check_nary_constraint_model_2",        "Model 2"),
    (check_out_of_domain_tuple,             lambda board: student_models.futoshiki_csp_model_2(board), "check_out_of_domain_tuple_model_2", "Model 2"),
    (test_model_2_construction_time,        student_models, "test_model_2_construction_time",       "Model 2"),
    (test_model2_construction_time_with_clues, student_models, "test_model2_construction_time_with_clues", "Model 2"),
    (test_model2_preassigned_rows,          student_models, "test_model2_preassigned_rows",         "Model 2"),
    (test_model2_preassigned_cols,          student_models, "test_model2_preassigned_cols",         "Model 2"),
    (test_model2_9x9_preassigned_tuples_correct, student_models, "test_model2_9x9_preassigned_tuples_correct", "Model 2"),
    (test_model2_9x9_tuple_count_with_clues, student_models, "test_model2_9x9_tuple_count_with_clues", "Model 2"),
    (test_model2_constraint_count,          student_models, "test_model2_constraint_count",         "Model 2"),

    # MRV
    (test_ord_mrv,          student_propagators,            "test_ord_mrv",                 "Ord"),
]