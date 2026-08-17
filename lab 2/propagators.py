"""
General notes to consider:
    * Propagator functions return a tuple of the shape
            True/False, [(Variable, value), ...]
      where False indicates that the propagator has reached
      a dead-end (in which case `bt_search` will backtrack),
      and True otherwise.

    * Propagator functions should not prune a value that has already
      been pruned.
      
    * `csp` is a required argument that represents the complete
      constraint satisfaction problem. Propagation functions will use
      this argument to access the variables and constraints that define
      the problem. Please read through the source code:
            `src/`
                `backtracking.py`
                `csp.py`
                `csp_constraint.py`
                `csp_variable.py`

    * `newVar` is an optional argument that represents the
      variable that has been most-recently assigned during search.
      If it is None, then the dedicated propagation algorithm will
      employ the logic described in the corresponding docstring
      to continue searching.
"""
from typing import Any
from collections import deque


def prop_BT(csp: 'CSP', newVar: 'Variable' = None) -> tuple[bool, list[tuple['Variable', Any]]]:
    """
    Return a tuple consisting of a boolean that represents whether we can
    continue propagating and the associated list of (Variable, Value) pairs
    that were pruned during propagation.

    If backtracking is called without a newly-instantiated variable,
    do nothing. That is, return (True, []).

    If backtracking is called with a newly-instantiated variable, check
    the satisfiability of every constraint whose scope contains newVar
    and whose variables are fully assigned.

    :param csp: the constraint satisfaction problem
    :param newVar: the most recently assigned variable
    """

    if not newVar:
        return True, []
    for constraint in csp.get_cons_with_var(newVar):
        if constraint.get_n_unassigned_vars() == 0:
            values = []
            variables = constraint.get_scope()
            for variable in variables:
                values.append(variable.get_assigned_value())
            if not constraint.check(values):
                return False, []
    return True, []


def prop_FC(csp: 'CSP', newVar: 'Variable' = None) -> tuple[bool, list[tuple['Variable', Any]]]:
    """
    Return a tuple consisting of a boolean that represents whether we can
    continue propagating and the associated list of (Variable, Value) pairs
    that were pruned during propagation.

    If forward-checking is called without a newly-instantiated variable,
    forward-check the satisfiability of all unary constraints: that is,
    constraints whose scope contains only one variable that is unassigned.

    If forward-checking is called with a newly-instantiated variable,
    forward-check the satisfiability of unary constraints whose scope
    contains newVar.

    :param csp: the constraint satisfaction problem
    :param newVar: the most recently assigned variable
    """
    pruned = []
    if not newVar:
        constraints = csp.get_all_cons() #use all constraints
    elif newVar:
        constraints = csp.get_cons_with_var(newVar) #use only constraints with newVar

    for constraint in constraints:
        if constraint.get_n_unassigned_vars() != 1: #only check constraints with exactly one unassigned variable
            continue

        ogvariable = constraint.get_unassigned_vars()[0]

        domain = list(ogvariable.cur_domain()) #use a snapshot of the domain as it may be pruned
        for value in domain:
            if not ogvariable.in_cur_domain(value): #to ensure theres no double pruning
                continue
            variables = []
            for variable in constraint.get_scope():
                if ogvariable == variable:
                    variables.append(value) #add the og variable assignment if its in scope
                else:
                    variables.append(variable.get_assigned_value()) #get all assigned values in the scope
            
            if not constraint.check(variables): #if the constraint isnt satisfied, prune the value
                ogvariable.prune_value(value)
                pruned.append((ogvariable, value))
                
        if ogvariable.cur_domain_size() == 0: #domain wipeout
            return False, pruned
        
    return True, pruned

def prop_GAC(csp: 'CSP', newVar: 'Variable' = None) -> tuple[bool, list[tuple['Variable', Any]]]:
    """
    Return a tuple consisting of a boolean that represents whether we can
    continue propagating and the associated list of (Variable, Value) pairs
    that were pruned during propagation.
    
    If GAC is called without a newly-instantiated variable, initialize the GAC
    queue with all constraints in csp.

    If GAC is called with a newly-instantiated variable, initialize the GAC
    queue with all constraints in csp that whose scope contains newVar.

    :param csp: the constraint satisfaction problem
    :param newVar: the most recently assigned variable
    """
    pruned = []
    if not newVar:
        constraints = deque(csp.get_all_cons()) #use all constraints
    elif newVar:
        constraints = deque(csp.get_cons_with_var(newVar)) #use only constraints with newVar

    in_queue = set(constraints)
    queue = deque(in_queue)

    while queue:
        constraint = queue.popleft()
        in_queue.discard(constraint)
        for variable in constraint.get_scope():
            if variable.is_assigned(): #doesnt need to be pruned
                continue
            domain = list(variable.cur_domain()) #use a snapshot of the domain as it may be pruned
            for value in domain:
                if not variable.in_cur_domain(value): #to ensure theres no double pruning
                    continue
                if not constraint.has_support(variable, value): #if the variable value pair has no support, prune it
                    variable.prune_value(value)
                    pruned.append((variable, value))
                    
                    if variable.cur_domain_size() == 0: #domain wipeout
                        return False, pruned
                    
                    for new_constraint in csp.get_cons_with_var(variable): #add all constraints with the variable to the queue
                        if new_constraint not in in_queue:
                            queue.append(new_constraint)
                            in_queue.add(new_constraint)
        
    return True, pruned

def degree(v, csp: 'CSP') -> int:
                return sum(
                    1 for con in csp.get_cons_with_var(v)
                    if any(not other.is_assigned() and other != v
                           for other in con.get_scope())
                )

def ord_mrv(csp: 'CSP') -> 'Variable':
    """
    Return the next variable to be assigned in csp according to the
    Minimum Remaining Values heuristic.

    That is, return the variable with the most constraint current domain,
    i.e. the variable with the fewest legal values.
    """
    minimum_domain = float('inf')
    minimum_variable = None
    for variable in csp.get_all_unasgn_vars():
        if variable.cur_domain_size() < minimum_domain: #if the domain is more restricted, use that variable
            minimum_domain = variable.cur_domain_size()
            minimum_variable = variable
            if minimum_domain == 1: #cant get better than 1
                break
        elif variable.cur_domain_size() == minimum_domain: #if theres a tie, break it by degree heuristic
            if degree(variable, csp) > degree(minimum_variable, csp):
                minimum_variable = variable
    return minimum_variable
