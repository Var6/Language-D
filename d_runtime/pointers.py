"""Pointer helpers for Language D.

The model is intentionally safer than raw pointers:
- A pointer always has ownership of one mutable slot.
- You can read/write only through explicit methods.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class Pointer(Generic[T]):
    """A safe, mutable reference to a single value."""

    _value: T

    def get(self) -> T:
        return self._value

    def set(self, value: T) -> None:
        self._value = value

    def map(self, fn: Callable[[T], T]) -> T:
        self._value = fn(self._value)
        return self._value

    def swap(self, other: "Pointer[T]") -> None:
        self._value, other._value = other._value, self._value


class NullablePointer(Pointer[Optional[T]]):
    """A pointer that can be empty (None)."""

    def is_null(self) -> bool:
        return self.get() is None


def addr(value: T) -> Pointer[T]:
    """Create a pointer from a value."""
    return Pointer(value)


def val(pointer: Pointer[T]) -> T:
    """Read a pointer's current value."""
    return pointer.get()


def set_val(pointer: Pointer[T], value: T) -> None:
    """Write to a pointer."""
    pointer.set(value)


def move(pointer: Pointer[Optional[T]]) -> Optional[T]:
    """Move out the value and leave None behind."""
    current = pointer.get()
    pointer.set(None)
    return current
