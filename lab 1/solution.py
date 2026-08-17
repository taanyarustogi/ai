#   You may only add standard python imports
#   You may not remove any imports.
#   You may not import or otherwise source any of your own files
from typing import Callable, Union

import os                       # For time functions
import math                     # For infinity

from src import (
    # For search engine implementations
    SearchEngine, SearchNode, SearchStatistics,
    # For Sokoban-specific implementations
    SokobanState,
    sokoban_goal_state,
    UP, DOWN, LEFT, RIGHT,
    # You may further import any constants you may need.
    # See `search_constants.py`
)

# SOKOBAN HEURISTICS
def heur_alternate(state: 'SokobanState') -> float:
    """
    Returns a heuristic value with the goal of improving upon
    the flaws inherent to a heuristic that uses Manhattan distance
    and produce a more accurate estimate of the distance from the
    current state to the goal state.

    You must explain your heuristic via inline comments.

    :param state: A SokobanState object representing the current
                  state in a game of Sokoban.
    :return: An estimate of the distance from the current
             SokobanState to the goal state.
    """
    total_distance = 0 #total distance from the boxes to their nearest storage points
    avaliable_storage = list(state.storage) #list of storage points that haven't been assigned
    unplaced_boxes = [] #list of boxes that havent been placed
    
    for box in state.boxes:
        if box in state.storage: #if the box is already on a storage point
            avaliable_storage.remove(box) #remove that storage point
        else:
            unplaced_boxes.append(box) #add the box to the unplaced list

    for box in unplaced_boxes: 
        #adding deadlocks - corners and walls

        #if the box is in a corner of the map or between walls or obstacles making a corner, it can never be moved
        up = box[1] == 0 or (box[0], box[1] - 1) in state.obstacles
        down = box[1] == state.height - 1 or (box[0], box[1] + 1) in state.obstacles
        left = box[0] == 0 or (box[0] - 1, box[1]) in state.obstacles
        right = box[0] == state.width - 1 or (box[0] + 1, box[1]) in state.obstacles
        if (up and left) or (up and right) or (down and left) or (down and right):
            return math.inf

        #if the box is against a wall and there is an obstacle next to it, it can never be moved
        if box[0] == 0 and ((box[0], box[1] - 1) in state.obstacles or (box[0], box[1] + 1) in state.obstacles):
            return math.inf
        if box[0] == state.width - 1 and ((box[0], box[1] - 1) in state.obstacles or (box[0], box[1] + 1) in state.obstacles):
            return math.inf
        if box[1] == 0 and ((box[0] - 1, box[1]) in state.obstacles or (box[0] + 1, box[1]) in state.obstacles):
            return math.inf
        if box[1] == state.height - 1 and ((box[0] - 1, box[1]) in state.obstacles or (box[0] + 1, box[1]) in state.obstacles):
            return math.inf
            
        #if the box is against a wall and there is an box next to it, it can never be moved
        if box[0] == 0 and ((box[0], box[1] - 1) in state.boxes or (box[0], box[1] + 1) in state.boxes):
            return math.inf
        if box[0] == state.width - 1 and ((box[0], box[1] - 1) in state.boxes or (box[0], box[1] + 1) in state.boxes):
            return math.inf
        if box[1] == 0 and ((box[0] - 1, box[1]) in state.boxes or (box[0] + 1, box[1]) in state.boxes):
            return math.inf
        if box[1] == state.height - 1 and ((box[0] - 1, box[1]) in state.boxes or (box[0] + 1, box[1]) in state.boxes):
            return math.inf
        
        #if the box is against a wall and there is no avaliable storage point against that wall, it can never be moved to storage
        if box[0] == 0:
            possible = 0
            for storage in avaliable_storage:
                if storage[0] == 0:
                    possible = 1
            if possible == 0:
                return math.inf
        if box[0] == state.width - 1:
            possible = 0
            for storage in avaliable_storage:
                if storage[0] == state.width - 1:
                    possible = 1
            if possible == 0:
                return math.inf
        if box[1] == 0:
            possible = 0
            for storage in avaliable_storage:
                if storage[1] == 0:
                    possible = 1
            if possible == 0:
                return math.inf
        if box[1] == state.height - 1:
            possible = 0
            for storage in avaliable_storage:
                if storage[1] == state.height - 1:
                    possible = 1
            if possible == 0:
                return math.inf
        
        closest_storage = None #the closest storage point to this box
        closest_distance = math.inf #initialise the closest distance to infinity
        for storage in avaliable_storage:
            distance = abs(box[0] - storage[0]) + abs(box[1] - storage[1]) #use the manhattan distance formula to calculate the distance
            
            #add penalities for obstacles, boxes and robots within the boundaries
            for obstacle in state.obstacles:
                if (obstacle[0] > min(box[0], storage[0]) and obstacle[0] < max(box[0], storage[0]) and obstacle[1] > min(box[1], storage[1]) and obstacle[1] < max(box[1], storage[1])):
                    distance += 3
            for other_box in state.boxes:
                if (other_box[0] > min(box[0], storage[0]) and other_box[0] < max(box[0], storage[0]) and other_box[1] > min(box[1], storage[1]) and other_box[1] < max(box[1], storage[1])):
                    distance += 1
            for robot in state.robots:
                if (robot[0] > min(box[0], storage[0]) and robot[0] < max(box[0], storage[0]) and robot[1] > min(box[1], storage[1]) and robot[1] < max(box[1], storage[1])):
                    distance += 1

            if distance < closest_distance:
                closest_storage = storage #if it is closer than the closest storage point so far, update it
                closest_distance = distance #if it is closer than the closest storage point so far, update it
        
        total_distance += closest_distance #add the closest distance for this box
        if closest_storage is not None:
            avaliable_storage.remove(closest_storage) #remove the closest storage point from the list of available storage points

    #add the distance from the robot to the nearest box
    shortest_distance = math.inf #initialise 
    for robot in state.robots:
        for box in state.boxes:
            robot_distance = abs(robot[0] - box[0]) + abs(robot[1] - box[1]) #use manhattan distance formula
            if robot_distance < shortest_distance:
                shortest_distance = robot_distance #if it is closer than the shortest distance so far, update it
    
    total_distance += shortest_distance

    return total_distance

def heur_zero(state: 'SokobanState') -> float:
    """
    This function is used in A* to perform a uniform cost search
    by returning zero.

    :param state: A SokobanState object representing the current
                  state in a game of Sokoban.
    :return: The zero value.
    """
    return 0

def heur_manhattan_distance(state: 'SokobanState') -> float:
    # IMPLEMENT
    """
    Returns an admissible - i.e. optimistic - heuristic by never
    overestimating the cost to transition from the current state to the goal state.
    The sum of the Manhattan distances between each box that has yet to be stored
    and the storage point nearest to it qualifies as such a heuristic.

    You may assume there are no obstacles on the grid when calculating distances.
    You must implement this function exactly as specified.

    :param state: A SokobanState object representing the current
                  state in a game of Sokoban.
    :return: An admissible estimate of the distance from the
             current SokobanState to the goal state.
    """
    total_distance = 0 #total distance from the boxes to their nearest storage points
    for box in state.boxes:
        closest_distance = math.inf #initialise the closest distance to infinity
        for storage in state.storage:
            distance = abs(box[0] - storage[0]) + abs(box[1] - storage[1]) #use the manhattan distance formula to calculate the distance
            if distance < closest_distance:
                closest_distance = distance #if it is closer than the closest storage point so far, update it
        total_distance += closest_distance #add the closest distance for this box
    return total_distance

def fval_function(node: 'SearchNode', weight: float) -> float:
    """
    Returns the f-value of the state contained in node
    based on weight, to be used in Anytime Weighted A* search.

    :param node: A SearchNode object containing a SokobanState object
    :param weight: The weight used in Anytime Weighted A* search.
    :return: The f-value of the state contained in node.
    """
    return node.gval + weight * node.hval #f(n) = g(n) + w * h(n)

# SEARCH ALGORITHMS
def weighted_astar(
        initial_state: 'SokobanState',
        heur_fn: Callable,
        weight: float,
        timebound: int) -> tuple[Union['SokobanState', bool], 'SearchStatistics']:
    """
    Returns a tuple of the goal SokobanState and a SearchStatistics object
    by implementing weighted A* search as defined in the handout.

    If no goal state is found, returns a tuple of False and a SearchStatistics
    object.

    :param initial_state: The initial SokobanState of the game of Sokoban.
    :param heur_fn: The heuristic function used in weighted A* search.
    :param weight: The weight used in calculating the heuristic.
    :param timebound: The time bound used in weighted A* search, in seconds.
    :return: A tuple consisting of the goal SokobanState or False if such a state
             is not found, and a SearchStatistics object.
    """
    wrapped_fval_function = (lambda sN: fval_function(sN, weight)) #define the f-val function
    search_engine = SearchEngine('custom', 'full') #create a search engine
    search_engine.init_search(initial_state, sokoban_goal_state, heur_fn, wrapped_fval_function) #initialize the search engine
    return search_engine.search(timebound) #perform the search and return the result

def iterative_astar( # uses f(n)
        initial_state: 'SokobanState',
        heur_fn: Callable,
        weight: float = 1,
        timebound: int = 5) -> tuple[Union['SokobanState', bool], 'SearchStatistics']:
    """
    Returns a tuple of the goal SokobanState and a SearchStatistics object
    by implementing realtime iterative A* search as defined in the handout.

    If no goal state is found, returns a tuple of False and a SearchStatistics
    object.

    Refer to test_alternate_fun in autograder.py to see how to initialize a search.

    :param initial_state: The initial SokobanState of the game of Sokoban.
    :param heur_fn: The heuristic function used in realtime iterative A* search.
    :param weight: The weight used in calculating the heuristic.
    :param timebound: The time bound used in realtime iterative A* search, in seconds.
    :return: A tuple consisting of the goal SokobanState or False if such a state
             is not found, and a SearchStatistics object.
    """
    ostart = os.times()[0] #get the start time

    #do the first search
    wrapped_fval_function = (lambda sN: fval_function(sN, weight)) #define the f-val function
    search_engine = SearchEngine('custom', 'full') #create a search engine
    search_engine.init_search(initial_state, sokoban_goal_state, heur_fn, wrapped_fval_function) #initialize the search engine
    (best_solution, best_search_stats) = search_engine.search((timebound)) #perform the search with the pruning
    
    #set costbound
    costbound = (math.inf, math.inf, math.inf) #set the costbound
    if best_solution is not False:
        costbound = (math.inf, math.inf, best_solution.gval) #set the cost bound to the f-val of the best solution

    while ((os.times()[0] - ostart) < timebound): #repeatedly call weighted A* until the time runs out

        wrapped_fval_function = (lambda sN: fval_function(sN, weight)) #define the f-val function
        search_engine.init_search(initial_state, sokoban_goal_state, heur_fn, wrapped_fval_function) #initialize the search engine
        (solution, stats) = search_engine.search((timebound - (os.times()[0] - ostart)), costbound) #perform the search with the pruning

        if solution is not False:
            if best_solution is False or (best_solution.gval > solution.gval): #if the solution is less cost than the best solution, replace
                best_solution = solution
                best_search_stats = stats
                costbound = (math.inf, math.inf, solution.gval) #reset the costbound
        weight = max(1, weight * 0.5) #decrease the weight each iteration, never less than 1
    
    return (best_solution, best_search_stats) #return the best solution found


def iterative_gbfs( # uses h(n)
        initial_state: 'SokobanState',
        heur_fn: Callable,
        timebound: int = 5) -> tuple[Union['SokobanState', bool], 'SearchStatistics']:
    """
    Returns a tuple of the goal SokobanState and a SearchStatistics object
    by implementing iterative greedy best-first search as defined in the handout.

    :param initial_state: The initial SokobanState of the game of Sokoban.
    :param heur_fn: The heuristic function used in iterative greedy best-first search.
    :param timebound: The time bound used in iterative greedy best-first search, in seconds.
    :return: A tuple consisting of the goal SokobanState or False if such a state
             is not found, and a SearchStatistics object.
    """
    ostart = os.times()[0] #get the start time

    #do the first search
    search_engine = SearchEngine('best_first', 'full') #create a search engine
    search_engine.init_search(initial_state, sokoban_goal_state, heur_fn) #initialize the search engine
    (best_solution, best_search_stats) = search_engine.search((timebound)) #perform the search with the pruning
    
    #set costbound
    costbound = (math.inf, math.inf, math.inf) #set the costbound
    if best_solution is not False:
        costbound =  (best_solution.gval, math.inf, math.inf) #set the cost bound to the f-val of the best solution

    while ((os.times()[0] - ostart) < timebound):
        search_engine.init_search(initial_state, sokoban_goal_state, heur_fn) #initialize the search engine
        (solution, stats) = search_engine.search((timebound - (os.times()[0] - ostart)), costbound) #perform the search with the pruning

        if solution is not False:
            if best_solution is False or (best_solution.gval > solution.gval): #if the solution is less cost than the best solution, replace
                best_solution = solution
                best_search_stats = stats
                costbound = (solution.gval, math.inf, math.inf) #reset the costbound
    
    return (best_solution, best_search_stats) #return the best solution found
