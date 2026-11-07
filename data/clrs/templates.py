import numpy as np

FAMILIES = {
    "insertion_sort": "sorting",
    "bubble_sort": "sorting",
    "heapsort": "sorting",
    "quicksort": "sorting",
    "minimum": "searching",
    "binary_search": "searching",
    "quickselect": "searching",
    "find_maximum_subarray_kadane": "divide_and_conquer",
    "activity_selector": "greedy",
    "task_scheduling": "greedy",
    "matrix_chain_order": "dynamic_programming",
    "lcs_length": "dynamic_programming",
    "optimal_bst": "dynamic_programming",
    "dfs": "graphs",
    "bfs": "graphs",
    "topological_sort": "graphs",
    "articulation_points": "graphs",
    "bridges": "graphs",
    "strongly_connected_components": "graphs",
    "mst_kruskal": "graphs",
    "mst_prim": "graphs",
    "bellman_ford": "graphs",
    "dijkstra": "graphs",
    "dag_shortest_paths": "graphs",
    "floyd_warshall": "graphs",
    "naive_string_matcher": "strings",
    "kmp_matcher": "strings",
    "segments_intersect": "geometry",
    "graham_scan": "geometry",
    "jarvis_march": "geometry",
}

ALPHABET = "abcdefghijklmnopqrstuvwxyz"


def _num(x, decimals):
    return f"{float(x):.{decimals}f}"


def _seq(values, decimals):
    return ", ".join(_num(x, decimals) for x in values)


def _letters(values):
    return "".join(ALPHABET[int(i)] for i in values)


def _edges(graph, decimals, directed, weighted):
    n = graph.shape[0]
    pairs = [(u, v) for u in range(n) for v in range(n) if u != v and graph[u, v] != 0 and (directed or u < v)]
    arrow = "->" if directed else "--"
    lines = [f"{u} {arrow} {v}" + (f" (weight {_num(graph[u, v], decimals)})" if weighted else "") for u, v in pairs]
    return "\n".join(lines) if lines else "(no edges)"


def _sequence_fields(inputs, cfg):
    return {"n": len(inputs[0]), "last": len(inputs[0]) - 1, "array": _seq(inputs[0], cfg["float_decimals"])}


def _search_fields(inputs, cfg):
    x, arr = inputs
    return {"n": len(arr), "last": len(arr) - 1, "array": _seq(arr, cfg["float_decimals"]),
            "target": _num(x, cfg["float_decimals"])}


def _quickselect_fields(inputs, cfg):
    return {**_sequence_fields(inputs, cfg), "rank": int(inputs[1])}


def _matrix_chain_fields(inputs, cfg):
    dims = [1 + int(x * cfg["matrix_dimension_scale"]) for x in inputs[0]]
    return {"n_matrices": len(dims) - 1, "dims": ", ".join(map(str, dims)),
            "matrices": "\n".join(f"A{i + 1}: {dims[i]} x {dims[i + 1]}" for i in range(len(dims) - 1))}


def _lcs_fields(inputs, cfg):
    return {"string_a": _letters(inputs[0]), "string_b": _letters(inputs[1])}


def _optimal_bst_fields(inputs, cfg):
    p, q = inputs
    d = cfg["float_decimals"]
    return {"n": len(p), "keys": "\n".join(f"k{i + 1}: {_num(x, d)}" for i, x in enumerate(p)),
            "dummies": "\n".join(f"d{i}: {_num(x, d)}" for i, x in enumerate(q))}


def _activity_fields(inputs, cfg):
    s, f = inputs
    d = cfg["float_decimals"]
    return {"n": len(s), "activities": "\n".join(f"Activity {i}: start {_num(a, d)}, finish {_num(b, d)}"
                                                 for i, (a, b) in enumerate(zip(s, f)))}


def _task_fields(inputs, cfg):
    deadlines, weights = inputs
    d = cfg["float_decimals"]
    return {"n": len(deadlines), "tasks": "\n".join(f"Task {i}: deadline {int(a)}, penalty {_num(b, d)}"
                                                    for i, (a, b) in enumerate(zip(deadlines, weights)))}


def _graph_fields(directed, weighted):
    def fields(inputs, cfg):
        graph = inputs[0]
        out = {"n": graph.shape[0], "last": graph.shape[0] - 1,
               "edges": _edges(graph, cfg["float_decimals"], directed, weighted)}
        return {**out, "source": int(inputs[1])} if len(inputs) > 1 else out
    return fields


def _matcher_fields(inputs, cfg):
    haystack, needle = inputs
    return {"text": _letters(haystack), "pattern": _letters(needle), "text_length": len(haystack),
            "pattern_length": len(needle)}


def _segments_fields(inputs, cfg):
    xs, ys = inputs
    d = cfg["float_decimals"]
    return {f"p{i + 1}": f"({_num(x, d)}, {_num(y, d)})" for i, (x, y) in enumerate(zip(xs, ys))}


def _hull_fields(inputs, cfg):
    xs, ys = inputs
    d = cfg["float_decimals"]
    return {"n": len(xs), "last": len(xs) - 1,
            "points": "\n".join(f"P{i}: ({_num(x, d)}, {_num(y, d)})" for i, (x, y) in enumerate(zip(xs, ys)))}


FIELDS = {
    "insertion_sort": _sequence_fields,
    "bubble_sort": _sequence_fields,
    "heapsort": _sequence_fields,
    "quicksort": _sequence_fields,
    "minimum": _sequence_fields,
    "binary_search": _search_fields,
    "quickselect": _quickselect_fields,
    "find_maximum_subarray_kadane": _sequence_fields,
    "activity_selector": _activity_fields,
    "task_scheduling": _task_fields,
    "matrix_chain_order": _matrix_chain_fields,
    "lcs_length": _lcs_fields,
    "optimal_bst": _optimal_bst_fields,
    "dfs": _graph_fields(directed=False, weighted=False),
    "bfs": _graph_fields(directed=False, weighted=False),
    "topological_sort": _graph_fields(directed=True, weighted=False),
    "articulation_points": _graph_fields(directed=False, weighted=False),
    "bridges": _graph_fields(directed=False, weighted=False),
    "strongly_connected_components": _graph_fields(directed=True, weighted=False),
    "mst_kruskal": _graph_fields(directed=False, weighted=True),
    "mst_prim": _graph_fields(directed=False, weighted=True),
    "bellman_ford": _graph_fields(directed=False, weighted=True),
    "dijkstra": _graph_fields(directed=False, weighted=True),
    "dag_shortest_paths": _graph_fields(directed=True, weighted=True),
    "floyd_warshall": _graph_fields(directed=False, weighted=True),
    "naive_string_matcher": _matcher_fields,
    "kmp_matcher": _matcher_fields,
    "segments_intersect": _segments_fields,
    "graham_scan": _hull_fields,
    "jarvis_march": _hull_fields,
}


ACTIONS = [
    "Run {name} on the {obj}{args}.",
    "Apply {name} to the {obj}{args}.",
    "Perform {name} on the {obj}{args}.",
    "Execute {name} on the {obj}{args}.",
    "Carry out {name} on the {obj}{args}.",
]

SEQUENCE_INTROS = [
    "Here is a list of {n} values: {array}",
    "You are given an array of {n} values:\n{array}",
    "Consider the array [{array}].",
    "Here is a sequence of values: {array}",
    "Given the following array of {n} values: {array}",
]

SORTED_INTROS = [
    "Here is a sorted array of {n} values: {array}",
    "You are given the sorted array [{array}].",
    "Consider the following ascending list of {n} values:\n{array}",
    "The array below is sorted in increasing order:\n{array}",
    "Given the following array of {n} values, sorted in non-decreasing order: {array}",
]

ACTIVITY_INTROS = [
    "There are {n} activities, each with a start and finish time:\n{activities}",
    "The following activities compete for a single resource:\n{activities}",
    "Here are {n} activities:\n{activities}",
    "Consider these activities and their start and finish times:\n{activities}",
    "You are given {n} activities:\n{activities}",
]

TASK_INTROS = [
    "There are {n} unit-time tasks, each with a deadline and a penalty for missing it:\n{tasks}",
    "The following unit-time tasks must be scheduled on a single processor:\n{tasks}",
    "Here are {n} unit-time tasks with deadlines and late penalties:\n{tasks}",
    "Consider these unit-length tasks:\n{tasks}",
    "You are given {n} tasks, each taking one unit of time:\n{tasks}",
]

MATRIX_CHAIN_INTROS = [
    "A chain of {n_matrices} matrices has the following dimensions:\n{matrices}",
    "The dimension sequence p = ({dims}) describes a chain of {n_matrices} matrices, where matrix Ai has size p[i-1] x p[i].",
    "Consider the matrix product A1 A2 ... A{n_matrices}, where:\n{matrices}",
    "Here are {n_matrices} matrices to be multiplied in sequence:\n{matrices}",
    "Matrices A1 to A{n_matrices} are to be multiplied in sequence, where matrix Ai has size d(i-1) x d(i) for the "
    "dimensions (d0, d1, ..., d{n_matrices}) = ({dims}).",
]

LCS_INTROS = [
    "Here are two strings: \"{string_a}\" and \"{string_b}\".",
    "The first string is \"{string_a}\" and the second is \"{string_b}\".",
    "String 1: \"{string_a}\"\nString 2: \"{string_b}\"",
    "Consider the strings \"{string_a}\" and \"{string_b}\".",
    "You are given two strings, \"{string_a}\" and \"{string_b}\".",
]

OPTIMAL_BST_INTROS = [
    "There are {n} keys k1 < k2 < ... < k{n} with search probabilities:\n{keys}\nDummy keys d0 to d{n}, for unsuccessful searches, have probabilities:\n{dummies}",
    "Sorted keys k1 to k{n} have search probabilities\n{keys}\nand dummy keys d0 to d{n}, standing for unsuccessful "
    "searches, have probabilities\n{dummies}",
    "{n} sorted keys have access probabilities:\n{keys}\nDummy keys d0 to d{n} represent failed searches, with probabilities:\n{dummies}",
    "Key probabilities:\n{keys}\nDummy-key probabilities:\n{dummies}",
    "Keys k1 < k2 < ... < k{n} and dummy keys d0 to d{n} have the following search probabilities.\nKeys:\n{keys}\n"
    "Dummy keys:\n{dummies}",
]

MATCHER_INTROS = [
    "Here is a text \"{text}\" and a pattern \"{pattern}\".",
    "Text: \"{text}\"\nPattern: \"{pattern}\"",
    "Consider the string \"{text}\" (length {text_length}) and the pattern \"{pattern}\" (length {pattern_length}).",
    "You are given the text \"{text}\" and the pattern \"{pattern}\".",
    "A text \"{text}\" and a pattern \"{pattern}\" are given.",
]

SEGMENTS_INTROS = [
    "The first segment goes from {p1} to {p2}, and the second goes from {p3} to {p4}.",
    "Consider the line segment with endpoints {p1} and {p2}, and the line segment with endpoints {p3} and {p4}.",
    "Two segments are given: one from {p1} to {p2}, and one from {p3} to {p4}.",
    "Here are two segments: {p1} to {p2}, and {p3} to {p4}.",
    "Let the segments be [{p1}, {p2}] and [{p3}, {p4}].",
]

HULL_INTROS = [
    "The following {n} points lie in the plane:\n{points}",
    "Here is a set of points:\n{points}",
    "Consider the points\n{points}",
    "Here are {n} points labelled P0 to P{last}:\n{points}",
    "You are given these points in the plane:\n{points}",
]


def _graph_intros(kind):
    return [
        f"Consider {kind} graph with {{n}} nodes, labelled 0 to {{last}}, and the following edges:\n{{edges}}",
        f"{kind[0].upper()}{kind[1:]} graph has nodes 0 through {{last}}. Its edges are:\n{{edges}}",
        f"You are given {kind} graph on the nodes 0, 1, ..., {{last}} with edge list:\n{{edges}}",
        f"Edges of {kind} graph whose nodes are numbered 0 to {{last}}:\n{{edges}}",
        f"Here is {kind} graph with {{n}} nodes (0 to {{last}}) and these edges:\n{{edges}}",
    ]


def _templates(intros, name, obj, ask, args=""):
    return [f"{intro}\n\n{action.format(name=name, obj=obj, args=args)} {ask}"
            for intro, action in zip(intros, ACTIONS)]


def _graph_templates(kind, name, ask, args=""):
    return _templates(_graph_intros(kind), name, "graph", ask, args)


SOURCE = " with source node {source}"

SORTED = "Report the array sorted in non-decreasing order."
LOMUTO = "Use the Lomuto partition scheme with the last element of each subarray as the pivot."
SHORTEST_PATHS = ("Report the shortest distance from node {source} to every node and each node's predecessor on a "
                  "shortest path (the source has none); if several predecessors give the same distance, choose the "
                  "lowest-numbered one.")
HULL = ("List the points on the convex hull in counterclockwise order, starting from the point with the lowest "
        "y-coordinate (the leftmost such point on ties).")
MATCH = "Report the 0-based index in the text of the first occurrence of the pattern."

TEMPLATES = {
    "insertion_sort": _templates(SEQUENCE_INTROS, "insertion sort", "array", SORTED),
    "bubble_sort": _templates(SEQUENCE_INTROS, "bubble sort", "array", SORTED),
    "heapsort": _templates(SEQUENCE_INTROS, "heapsort", "array", SORTED),
    "quicksort": _templates(SEQUENCE_INTROS, "quicksort", "array", f"{LOMUTO} {SORTED}"),
    "minimum": _templates(SEQUENCE_INTROS, "a linear scan for the minimum", "array",
                          "Report the 0-based index of the minimum element; if the minimum value occurs more than "
                          "once, report the smallest such index."),
    "binary_search": _templates(SORTED_INTROS, "binary search", "array",
                                "The target need not be in the array: report the smallest 0-based index whose element "
                                "is greater than or equal to {target}, or {n} (the length of the array) if every "
                                "element is smaller than {target}.", " to find {target}"),
    "quickselect": _templates(SEQUENCE_INTROS, "quickselect", "array",
                              f"{LOMUTO} Report its value.",
                              " to find the element at 0-based index {rank} of the sorted array"),
    "find_maximum_subarray_kadane": _templates(SEQUENCE_INTROS, "Kadane's maximum-subarray algorithm", "array",
                                               "Report the 0-based start and end indices (inclusive) of a non-empty "
                                               "contiguous subarray with the largest sum, and that sum; if several "
                                               "subarrays tie, choose the one that ends earliest, then the one that "
                                               "starts earliest."),
    "activity_selector": _templates(ACTIVITY_INTROS, "the greedy activity-selection algorithm", "activities",
                                    "Consider activities in increasing order of finish time (lower activity number "
                                    "first on ties) and select one whenever it starts no earlier than the last "
                                    "selected activity finishes. List the selected activities by number, in "
                                    "increasing order."),
    "task_scheduling": _templates(TASK_INTROS, "the greedy task-scheduling algorithm", "tasks",
                                  "Tasks run one after another starting at time 0. Consider tasks in decreasing order "
                                  "of penalty (lower task number first on ties) and accept a task whenever all "
                                  "accepted tasks can still finish by their deadlines. List the accepted (on-time) "
                                  "tasks by number, in increasing order, and give the total penalty of the late "
                                  "tasks."),
    "matrix_chain_order": _templates(MATRIX_CHAIN_INTROS, "the matrix-chain-order dynamic-programming algorithm",
                                     "matrix chain",
                                     "Report the minimum number of scalar multiplications and an optimal "
                                     "parenthesization of the matrices A1 to A{n_matrices}; when several split points "
                                     "give the same cost, use the smallest one."),
    "lcs_length": _templates(LCS_INTROS, "the longest-common-subsequence dynamic-programming algorithm", "two strings",
                             "Report the length of a longest common subsequence and one such subsequence, traced back "
                             "from the ends of both strings: when the last characters match, keep them; otherwise, if "
                             "dropping the last character of the first string keeps the LCS length, drop it; else "
                             "drop the last character of the second string."),
    "optimal_bst": _templates(OPTIMAL_BST_INTROS, "the optimal-binary-search-tree dynamic-programming algorithm",
                              "keys",
                              "Report the minimum expected search cost (the sum over all keys and dummy keys of "
                              "probability times depth + 1, with the root at depth 0) and the optimal tree, given as "
                              "the root of every subtree; when several roots give the same cost, choose the "
                              "lowest-numbered key."),
    "dfs": _graph_templates("an undirected", "depth-first search",
                            "Start from node 0 and visit neighbors in increasing order. Report the order in which "
                            "nodes are discovered and each node's parent in the depth-first tree (node 0, the root, "
                            "has no parent)."),
    "bfs": _graph_templates("an undirected", "breadth-first search",
                            "Visit neighbors in increasing order; each node's parent is the node that first discovers "
                            "it. Report each node's distance (number of edges) from node {source} and its "
                            "parent in the breadth-first tree (the source has no parent).", SOURCE),
    "topological_sort": _graph_templates("a directed acyclic", "the DFS-based topological sort",
                                         "Start from node 0, restart at the lowest-numbered unvisited node once the "
                                         "current search finishes, and visit out-neighbors in increasing order. "
                                         "Report the resulting topological order, i.e. the nodes in decreasing order "
                                         "of finish time."),
    "articulation_points": _graph_templates("an undirected", "the DFS-based articulation-points algorithm",
                                            "Start the depth-first search from node 0, visit neighbors in increasing "
                                            "order, and use discovery times and low values to identify articulation "
                                            "points. List all articulation points in increasing order, or say there "
                                            "are none."),
    "bridges": _graph_templates("an undirected", "the DFS-based bridge-finding algorithm",
                                "Start the depth-first search from node 0, visit neighbors in increasing order, and "
                                "use discovery times and low values to identify bridges. List every bridge as an edge "
                                "u -- v with u < v, sorted by u and then v, or say there are none."),
    "strongly_connected_components": _graph_templates("a directed",
                                                      "Kosaraju's strongly-connected-components algorithm",
                                                      "Run a depth-first search from node 0, restarting at the "
                                                      "lowest-numbered unvisited node once the current search "
                                                      "finishes and visiting out-neighbors in increasing order; then "
                                                      "run a depth-first search on the transposed graph, starting "
                                                      "each search at the unvisited node with the latest finish time. "
                                                      "List the strongly connected components, each as its nodes in "
                                                      "increasing order, ordering the components by their smallest "
                                                      "node."),
    "mst_kruskal": _graph_templates("a weighted undirected", "Kruskal's minimum-spanning-tree algorithm",
                                    "Process edges in increasing order of weight, breaking ties by the endpoint pair "
                                    "(u, v) with u < v in lexicographic order, and add an edge unless its endpoints "
                                    "are already connected by edges added so far. List the minimum-spanning-tree "
                                    "edges, each as u -- v with u < v, in the order they are added, and give the "
                                    "total weight."),
    "mst_prim": _graph_templates("a weighted undirected", "Prim's minimum-spanning-tree algorithm",
                                 "At each step, extract the node with the smallest key (lowest-numbered on ties), scan "
                                 "its neighbors in increasing order, and, for each neighbor not yet in the tree, "
                                 "update its key and parent when the connecting edge is strictly lighter than its "
                                 "current key. Report each node's parent in the minimum spanning tree (the root has "
                                 "none) and the total weight.", " with root node {source}"),
    "bellman_ford": _graph_templates("a weighted undirected", "the Bellman-Ford algorithm",
                                     "In each pass, go through the edges in the order listed and relax each one in "
                                     "both directions; make up to {last} passes, stopping early once a pass changes "
                                     f"nothing. {SHORTEST_PATHS}", SOURCE),
    "dijkstra": _graph_templates("a weighted undirected", "Dijkstra's algorithm",
                                 "At each step, extract the unvisited node with the smallest tentative distance "
                                 "(lowest-numbered on ties), relax the edges to its neighbors in increasing order, and "
                                 "update a distance and predecessor only on strict improvement. Report the shortest "
                                 "distance from node {source} to every node and each node's predecessor (the source "
                                 "has none).", SOURCE),
    "dag_shortest_paths": _graph_templates("a weighted directed acyclic", "the DAG shortest-paths algorithm",
                                           "First find a topological order of the nodes; then, taking the nodes in "
                                           "that order, relax each one's outgoing edges in increasing order of target "
                                           f"node. {SHORTEST_PATHS}", SOURCE),
    "floyd_warshall": _graph_templates("a weighted undirected", "the Floyd-Warshall algorithm",
                                       "For each intermediate node k = 0, 1, ..., {last} in turn, update every "
                                       "distance d[i][j] to min(d[i][j], d[i][k] + d[k][j]). The distances are "
                                       "symmetric, so report the shortest-path distance d[i][j] only for each pair of "
                                       "nodes i < j."),
    "naive_string_matcher": _templates(MATCHER_INTROS, "the naive string-matching algorithm", "text and pattern",
                                       MATCH),
    "kmp_matcher": _templates(MATCHER_INTROS, "the Knuth-Morris-Pratt (KMP) algorithm", "text and pattern",
                              "First compute the prefix function of the pattern; then scan the text, using the prefix "
                              f"function to shift the pattern after a mismatch. {MATCH}"),
    "segments_intersect": _templates(SEGMENTS_INTROS, "the segments-intersect algorithm", "two segments",
                                     "Compute the cross product that gives the orientation of each segment's endpoints "
                                     "relative to the other segment, and decide from their signs. Answer whether the "
                                     "two segments intersect (yes or no)."),
    "graham_scan": _templates(HULL_INTROS, "Graham's scan", "points",
                              f"{HULL} Sort the other points by polar angle around that starting point, then process "
                              "them in that order with a stack, popping the top while the last three points do not "
                              "make a left turn."),
    "jarvis_march": _templates(HULL_INTROS, "Jarvis's march (gift wrapping)", "points",
                               f"{HULL} From that starting point, repeatedly choose as the next hull point the one "
                               "such that every other point lies to the left of the edge to it, until you return to "
                               "the start."),
}


def render(algorithm: str, inputs, template_id: int, cfg: dict) -> str:
    return TEMPLATES[algorithm][template_id].format(**FIELDS[algorithm](inputs, cfg))


def serialise(inputs):
    return [x.tolist() if isinstance(x, np.ndarray) else x.item() if isinstance(x, np.generic) else x for x in inputs]
