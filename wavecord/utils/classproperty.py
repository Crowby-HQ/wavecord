# SPDX-License-Identifier: MIT
"""Utility descriptor for class-level properties."""

from __future__ import annotations

from typing import Any, Callable, Generic, Optional, Type, TypeVar, overload

__all__ = ("classproperty",)

_T = TypeVar("_T")
_ClsT = TypeVar("_ClsT")


class classproperty(Generic[_T]):
    """Descriptor that works like :func:`property` but on the class itself.

    Example
    -------
    .. code-block:: python

        class Foo:
            _items: ClassVar[list[str]] = []

            @classproperty
            def items(cls) -> list[str]:
                return cls._items
    """

    def __init__(self, func: Callable[[Any], _T]) -> None:
        self._func = func

    @overload
    def __get__(self, obj: None, cls: Type[_ClsT]) -> _T: ...

    @overload
    def __get__(self, obj: _ClsT, cls: Optional[Type[_ClsT]] = ...) -> _T: ...

    def __get__(self, obj: Any, cls: Any = None) -> _T:
        if cls is None:
            cls = type(obj)
        return self._func(cls)
