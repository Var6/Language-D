"""Frequently used algorithms for Language D."""

from __future__ import annotations

import heapq
from collections import deque
from typing import Dict, Hashable, Iterable, List, Sequence, Tuple, TypeVar

T = TypeVar("T")
Node = TypeVar("Node", bound=Hashable)


def binary_search(sorted_values: Sequence[T], target: T) -> int:
    lo = 0
    hi = len(sorted_values) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        value = sorted_values[mid]
        if value == target:
            return mid
        if value < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def quick_sort(values: Iterable[T]) -> List[T]:
    arr = list(values)
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    mid = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + mid + quick_sort(right)


def bfs(graph: Dict[Node, List[Node]], start: Node) -> List[Node]:
    visited = set([start])
    order: List[Node] = []
    queue = deque([start])

    while queue:
        node = queue.popleft()
        order.append(node)
        for nxt in graph.get(node, []):
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)

    return order


def dijkstra(graph: Dict[Node, List[Tuple[Node, float]]], start: Node):
    distances: Dict[Node, float] = {start: 0.0}
    heap: List[Tuple[float, Node]] = [(0.0, start)]

    while heap:
        dist, node = heapq.heappop(heap)
        if dist > distances.get(node, float("inf")):
            continue
        for nxt, weight in graph.get(node, []):
            candidate = dist + weight
            if candidate < distances.get(nxt, float("inf")):
                distances[nxt] = candidate
                heapq.heappush(heap, (candidate, nxt))

    return distances
