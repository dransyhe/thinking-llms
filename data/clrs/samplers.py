# Copyright 2021 DeepMind Technologies Limited. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
# Input generators adapted from clrs/_src/samplers.py of
# https://github.com/google-deepmind/clrs (commit 6d5728b), reduced to numpy. Unlike CLRS, graphs have no self-loops,
# the articulation/bridge and MST samplers use p=0.4 and 0.5 instead of 0.2 (an undirected edge needs both coin flips,
# so p=0.2 gives density 0.04 and the graph is almost never connected), and the SCC sampler scales its community count
# with the graph size and links communities more densely, so that small SCC graphs are not near-empty. DFS samples an
# undirected graph, as BFS does, instead of a directed one. Quickselect samples a uniform rank to select, where CLRS
# always selects the median (rank n // 2). The string matchers draw a pattern of 2 to 4 characters instead of
# length // 5, which is a single character for most lengths and leaves the KMP prefix function trivial.

import itertools

import numpy as np


class Sampler:

    def __init__(self, rng: np.random.RandomState, truncate_decimals: int):
        self._rng = rng
        self._truncate_decimals = truncate_decimals

    def _trunc(self, x):
        scale = 10 ** self._truncate_decimals
        return np.trunc(x * scale) / scale

    def _trunc_array(self, data):
        return [self._trunc(x) if isinstance(x, float) or (isinstance(x, np.ndarray) and np.issubdtype(x.dtype, np.floating)) else x
                for x in data]

    def sample(self, length: int, **kwargs):
        return self._trunc_array(self._sample_data(length, **kwargs))

    def _random_sequence(self, length, low=0.0, high=1.0):
        return self._rng.uniform(low=low, high=high, size=(length,))

    def _random_string(self, length, chars=4):
        return self._rng.randint(0, high=chars, size=(length,))

    def _random_er_graph(self, nb_nodes, p=0.5, directed=False, acyclic=False, weighted=False, low=0.0, high=1.0):
        mat = self._rng.binomial(1, p, size=(nb_nodes, nb_nodes))
        if not directed:
            mat *= np.transpose(mat)
        elif acyclic:
            mat = np.triu(mat, k=1)
            p = self._rng.permutation(nb_nodes)
            mat = mat[p, :][:, p]
        if weighted:
            weights = self._rng.uniform(low=low, high=high, size=(nb_nodes, nb_nodes))
            if not directed:
                weights *= np.transpose(weights)
                weights = np.sqrt(weights + 1e-3)
            mat = mat.astype(float) * weights
        np.fill_diagonal(mat, 0)
        return mat

    def _random_community_graph(self, nb_nodes, k=4, p=0.5, eps=0.01, directed=False, acyclic=False, weighted=False,
                                low=0.0, high=1.0):
        mat = np.zeros((nb_nodes, nb_nodes))
        if k > nb_nodes:
            raise ValueError(f"Cannot generate graph of too many ({k}) communities.")
        los, his = [], []
        lo = 0
        for i in range(k):
            hi = nb_nodes if i == k - 1 else lo + nb_nodes // k
            mat[lo:hi, lo:hi] = self._random_er_graph(hi - lo, p=p, directed=directed, acyclic=acyclic,
                                                      weighted=weighted, low=low, high=high)
            los.append(lo)
            his.append(hi)
            lo = hi
        toggle = self._random_er_graph(nb_nodes, p=eps, directed=directed, acyclic=acyclic, weighted=weighted,
                                       low=low, high=high)
        for i in range(k):
            for j in range(i):
                toggle[los[i]:his[i], los[j]:his[j]] *= 0
        mat = np.where(toggle > 0.0, (1.0 - (mat > 0.0)) * toggle, mat)
        p = self._rng.permutation(nb_nodes)
        return mat[p, :][:, p]


class SortingSampler(Sampler):

    def _sample_data(self, length, low=0.0, high=1.0):
        return [self._random_sequence(length=length, low=low, high=high)]


class SearchSampler(Sampler):

    def _sample_data(self, length, low=0.0, high=1.0):
        arr = self._random_sequence(length=length, low=low, high=high)
        arr.sort()
        return [self._rng.uniform(low=low, high=high), arr]


class QuickselectSampler(Sampler):

    def _sample_data(self, length, low=0.0, high=1.0):
        return [self._random_sequence(length=length, low=low, high=high), self._rng.randint(length)]


class MaxSubarraySampler(Sampler):

    def _sample_data(self, length, low=-1.0, high=1.0):
        return [self._random_sequence(length=length, low=low, high=high)]


class LCSSampler(Sampler):

    def _sample_data(self, length, length_2=None, chars=4):
        if length_2 is None:
            length_2 = length // 2
            length -= length_2
        return [self._random_string(length=length, chars=chars), self._random_string(length=length_2, chars=chars)]


class OptimalBSTSampler(Sampler):

    def _sample_data(self, length):
        arr = self._random_sequence(length=2 * length + 1, low=0.0, high=1.0)
        arr /= np.sum(arr)
        return [arr[:length], arr[length:]]


class ActivitySampler(Sampler):

    def _sample_data(self, length, low=0.0, high=1.0):
        arr_1 = self._random_sequence(length=length, low=low, high=high)
        arr_2 = self._random_sequence(length=length, low=low, high=high)
        return [np.minimum(arr_1, arr_2), np.maximum(arr_1, arr_2)]


class TaskSampler(Sampler):

    def _sample_data(self, length, max_deadline=None, low=0.0, high=1.0):
        d = self._random_string(length=length, chars=length if max_deadline is None else max_deadline) + 1
        return [d, self._random_sequence(length=length, low=low, high=high)]


class DfsSampler(Sampler):

    def _sample_data(self, length, p=(0.5,)):
        return [self._random_er_graph(nb_nodes=length, p=self._rng.choice(p), directed=False, acyclic=False,
                                      weighted=False)]


class BfsSampler(Sampler):

    def _sample_data(self, length, p=(0.5,)):
        graph = self._random_er_graph(nb_nodes=length, p=self._rng.choice(p), directed=False, acyclic=False,
                                      weighted=False)
        return [graph, self._rng.choice(length)]


class TopoSampler(Sampler):

    def _sample_data(self, length, p=(0.5,)):
        return [self._random_er_graph(nb_nodes=length, p=self._rng.choice(p), directed=True, acyclic=True,
                                      weighted=False)]


class ArticulationSampler(Sampler):

    def _sample_data(self, length, p=(0.4,)):
        return [self._random_er_graph(nb_nodes=length, p=self._rng.choice(p), directed=False, acyclic=False,
                                      weighted=False)]


class MSTSampler(Sampler):

    def _sample_data(self, length, p=(0.5,), low=0.0, high=1.0):
        return [self._random_er_graph(nb_nodes=length, p=self._rng.choice(p), directed=False, acyclic=False,
                                      weighted=True, low=low, high=high)]


class BellmanFordSampler(Sampler):

    def _sample_data(self, length, p=(0.5,), low=0.0, high=1.0):
        graph = self._random_er_graph(nb_nodes=length, p=self._rng.choice(p), directed=False, acyclic=False,
                                      weighted=True, low=low, high=high)
        return [graph, self._rng.choice(length)]


class DAGPathSampler(Sampler):

    def _sample_data(self, length, p=(0.5,), low=0.0, high=1.0):
        graph = self._random_er_graph(nb_nodes=length, p=self._rng.choice(p), directed=True, acyclic=True,
                                      weighted=True, low=low, high=high)
        return [graph, self._rng.choice(length)]


class FloydWarshallSampler(Sampler):

    def _sample_data(self, length, p=(0.5,), low=0.0, high=1.0):
        return [self._random_er_graph(nb_nodes=length, p=self._rng.choice(p), directed=False, acyclic=False,
                                      weighted=True, low=low, high=high)]


class SccSampler(Sampler):

    def _sample_data(self, length, k=None, p=(0.5,), eps=0.1):
        k = min(4, max(2, length // 3)) if k is None else k
        return [self._random_community_graph(nb_nodes=length, k=k, p=self._rng.choice(p), eps=eps, directed=True,
                                             acyclic=False, weighted=False)]


class MatcherSampler(Sampler):

    def _sample_data(self, length, length_needle=None, chars=4):
        if length_needle is None:
            # The text must be longer than the pattern for the pattern to be embedded below.
            length_needle = self._rng.randint(2, max(2, min(4, (length - 1) // 2)) + 1)
        elif length_needle < 0:
            length_needle = self._rng.randint(1, high=1 - length_needle)
        length_haystack = length - length_needle
        needle = self._random_string(length=length_needle, chars=chars)
        haystack = self._random_string(length=length_haystack, chars=chars)
        embed_pos = self._rng.choice(length_haystack - length_needle)
        haystack[embed_pos:embed_pos + length_needle] = needle
        return [haystack, needle]


class SegmentsSampler(Sampler):

    def _sample_data(self, length, low=0.0, high=1.0):
        def ccw(x_a, y_a, x_b, y_b, x_c, y_c):
            return (y_c - y_a) * (x_b - x_a) > (y_b - y_a) * (x_c - x_a)

        def intersect(xs, ys):
            return (ccw(xs[0], ys[0], xs[2], ys[2], xs[3], ys[3]) != ccw(xs[1], ys[1], xs[2], ys[2], xs[3], ys[3])
                    and ccw(xs[0], ys[0], xs[1], ys[1], xs[2], ys[2]) != ccw(xs[0], ys[0], xs[1], ys[1], xs[3], ys[3]))

        coin_flip = self._rng.binomial(1, 0.5)
        xs = self._random_sequence(length=4, low=low, high=high)
        ys = self._random_sequence(length=4, low=low, high=high)
        while intersect(xs, ys) != coin_flip:
            xs = self._random_sequence(length=4, low=low, high=high)
            ys = self._random_sequence(length=4, low=low, high=high)
        return [xs, ys]


def _is_collinear(point_1, point_2, point_3, eps):
    v_1, v_2 = point_2 - point_1, point_3 - point_1
    return bool(abs(v_1[0] * v_2[1] - v_1[1] * v_2[0]) < eps)


class ConvexHullSampler(Sampler):

    def _sample_data(self, length, origin_x=0.0, origin_y=0.0, radius=2.0, collinearity_resampling_attempts=1000,
                     collineararity_eps=1e-12):
        for _ in range(collinearity_resampling_attempts):
            thetas = self._random_sequence(length=length, low=0.0, high=2.0 * np.pi)
            rs = radius * np.sqrt(self._random_sequence(length=length, low=0.0, high=1.0))
            xs = self._trunc(rs * np.cos(thetas) + origin_x)
            ys = self._trunc(rs * np.sin(thetas) + origin_y)
            points = np.stack([xs, ys], axis=1)
            if not any(_is_collinear(a, b, c, collineararity_eps) for a, b, c in itertools.combinations(points, 3)):
                return [xs, ys]
        raise RuntimeError(f"Could not sample {length} stable points within {collinearity_resampling_attempts} tries.")


SAMPLERS = {
    "insertion_sort": SortingSampler,
    "bubble_sort": SortingSampler,
    "heapsort": SortingSampler,
    "quicksort": SortingSampler,
    "quickselect": QuickselectSampler,
    "minimum": SortingSampler,
    "binary_search": SearchSampler,
    "find_maximum_subarray_kadane": MaxSubarraySampler,
    "matrix_chain_order": SortingSampler,
    "lcs_length": LCSSampler,
    "optimal_bst": OptimalBSTSampler,
    "activity_selector": ActivitySampler,
    "task_scheduling": TaskSampler,
    "dfs": DfsSampler,
    "topological_sort": TopoSampler,
    "strongly_connected_components": SccSampler,
    "articulation_points": ArticulationSampler,
    "bridges": ArticulationSampler,
    "bfs": BfsSampler,
    "mst_kruskal": MSTSampler,
    "mst_prim": BellmanFordSampler,
    "bellman_ford": BellmanFordSampler,
    "dag_shortest_paths": DAGPathSampler,
    "dijkstra": BellmanFordSampler,
    "floyd_warshall": FloydWarshallSampler,
    "naive_string_matcher": MatcherSampler,
    "kmp_matcher": MatcherSampler,
    "segments_intersect": SegmentsSampler,
    "graham_scan": ConvexHullSampler,
    "jarvis_march": ConvexHullSampler,
}
