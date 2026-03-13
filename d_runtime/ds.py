"""Common data structures for Language D."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Generic, Iterable, Iterator, List, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")
T = TypeVar("T")


class Vector(Generic[T]):
    def __init__(self, values: Optional[Iterable[T]] = None) -> None:
        self._data: List[T] = list(values or [])

    def push(self, value: T) -> None:
        self._data.append(value)

    def pop(self) -> T:
        return self._data.pop()

    def get(self, index: int) -> T:
        return self._data[index]

    def set(self, index: int, value: T) -> None:
        self._data[index] = value

    def size(self) -> int:
        return len(self._data)

    def to_list(self) -> List[T]:
        return list(self._data)

    def __iter__(self) -> Iterator[T]:
        return iter(self._data)

    def __repr__(self) -> str:
        return f"Vector({self._data!r})"


class Stack(Generic[T]):
    def __init__(self) -> None:
        self._data: List[T] = []

    def push(self, value: T) -> None:
        self._data.append(value)

    def pop(self) -> T:
        return self._data.pop()

    def peek(self) -> T:
        return self._data[-1]

    def is_empty(self) -> bool:
        return not self._data


class Queue(Generic[T]):
    def __init__(self) -> None:
        self._data: Deque[T] = deque()

    def enqueue(self, value: T) -> None:
        self._data.append(value)

    def dequeue(self) -> T:
        return self._data.popleft()

    def is_empty(self) -> bool:
        return not self._data


@dataclass
class _Node(Generic[T]):
    value: T
    next: Optional["_Node[T]"] = None


class LinkedList(Generic[T]):
    def __init__(self) -> None:
        self._head: Optional[_Node[T]] = None
        self._tail: Optional[_Node[T]] = None

    def append(self, value: T) -> None:
        node = _Node(value)
        if self._head is None:
            self._head = node
            self._tail = node
            return
        assert self._tail is not None
        self._tail.next = node
        self._tail = node

    def to_list(self) -> List[T]:
        out: List[T] = []
        cur = self._head
        while cur is not None:
            out.append(cur.value)
            cur = cur.next
        return out


class HashMap(Generic[K, V]):
    def __init__(self) -> None:
        self._data: Dict[K, V] = {}

    def put(self, key: K, value: V) -> None:
        self._data[key] = value

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        return self._data.get(key, default)

    def remove(self, key: K) -> None:
        if key in self._data:
            del self._data[key]

    def contains(self, key: K) -> bool:
        return key in self._data

    def items(self):
        return self._data.items()
