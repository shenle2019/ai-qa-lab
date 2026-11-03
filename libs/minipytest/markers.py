"""Markers, parametrization specs, and the -m expression parser."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence

from .errors import UsageError


@dataclass(frozen=True)
class Mark:
    name: str
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Param:
    values: tuple[Any, ...]
    id: str | None = None
    marks: tuple[Mark, ...] = ()


@dataclass(frozen=True)
class ParametrizeSpec:
    argnames: tuple[str, ...]
    argvalues: tuple[Any, ...]
    ids: tuple[str | None, ...] | None = None


class MarkDecorator:
    """Supports @mark.smoke, @mark.skip('reason'), and @mark('tag', ...)."""

    def __init__(self, name: str) -> None:
        self.name = name

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if len(args) == 1 and not kwargs and callable(args[0]) and not isinstance(args[0], Mark):
            return self._attach(args[0], Mark(self.name))

        mark = Mark(self.name, tuple(args), dict(kwargs))

        def decorate(func: Any) -> Any:
            return self._attach(func, mark)

        return decorate

    @staticmethod
    def _attach(func: Any, mark: Mark) -> Any:
        marks = list(getattr(func, "__minipytest_marks__", ()))
        marks.append(mark)
        setattr(func, "__minipytest_marks__", tuple(marks))
        return func


class _MarkGenerator:
    def __getattr__(self, name: str) -> MarkDecorator:
        if name.startswith("_"):
            raise AttributeError(name)
        return MarkDecorator(name)

    def __call__(self, name: str, *args: Any, **kwargs: Any) -> Any:
        return MarkDecorator(name)(*args, **kwargs)


mark = _MarkGenerator()


def attach_mark(func: Any, mark_obj: Mark) -> Any:
    return MarkDecorator._attach(func, mark_obj)


def get_marks(obj: Any) -> tuple[Mark, ...]:
    return tuple(getattr(obj, "__minipytest_marks__", ()))


def parametrize(
    argnames: str | Sequence[str],
    argvalues: Iterable[Any],
    *,
    ids: Sequence[str | None] | None = None,
) -> Callable[[Any], Any]:
    if isinstance(argnames, str):
        names = tuple(part.strip() for part in argnames.split(",") if part.strip())
    else:
        names = tuple(str(part).strip() for part in argnames if str(part).strip())
    if not names:
        raise UsageError("parametrize() needs at least one argument name")

    values = tuple(argvalues)
    id_values = tuple(ids) if ids is not None else None
    if id_values is not None and len(id_values) != len(values):
        raise UsageError("parametrize() ids length must match argvalues length")

    spec = ParametrizeSpec(names, values, id_values)

    def decorate(func: Any) -> Any:
        specs = list(getattr(func, "__minipytest_parametrize__", ()))
        specs.append(spec)
        setattr(func, "__minipytest_parametrize__", tuple(specs))
        return func

    return decorate


def param(*values: Any, id: str | None = None, marks: Sequence[Mark] = ()) -> Param:
    return Param(tuple(values), id=id, marks=tuple(marks))


_TOKEN_RE = re.compile(r"\s*(\(|\)|\band\b|\bor\b|\bnot\b|[A-Za-z0-9_-]+)")
_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def parse_marker_expr(expr: str | None) -> Callable[[set[str]], bool]:
    """Parse -m syntax: or < and < not < parentheses < marker name."""
    if not expr or not expr.strip():
        return lambda names: True

    tokens: list[str] = []
    pos = 0
    while pos < len(expr):
        match = _TOKEN_RE.match(expr, pos)
        if not match:
            raise UsageError(f"invalid marker expression near: {expr[pos:]!r}")
        tokens.append(match.group(1))
        pos = match.end()
        while pos < len(expr) and expr[pos].isspace():
            pos += 1

    index = 0

    def peek() -> str | None:
        return tokens[index] if index < len(tokens) else None

    def take() -> str:
        nonlocal index
        token = peek()
        if token is None:
            raise UsageError("unexpected end of marker expression")
        index += 1
        return token

    def parse_or() -> Callable[[set[str]], bool]:
        left = parse_and()
        while peek() == "or":
            take()
            right = parse_and()
            previous = left
            left = lambda names, a=previous, b=right: a(names) or b(names)
        return left

    def parse_and() -> Callable[[set[str]], bool]:
        left = parse_not()
        while peek() == "and":
            take()
            right = parse_not()
            previous = left
            left = lambda names, a=previous, b=right: a(names) and b(names)
        return left

    def parse_not() -> Callable[[set[str]], bool]:
        if peek() == "not":
            take()
            inner = parse_not()
            return lambda names, f=inner: not f(names)
        return parse_atom()

    def parse_atom() -> Callable[[set[str]], bool]:
        token = peek()
        if token == "(":
            take()
            inner = parse_or()
            if peek() != ")":
                raise UsageError("missing closing parenthesis in marker expression")
            take()
            return inner
        if token is None:
            raise UsageError("unexpected end of marker expression")
        if not _NAME_RE.match(token):
            raise UsageError(f"invalid marker token: {token!r}")
        take()
        marker_name = token
        return lambda names, n=marker_name: n in names

    result = parse_or()
    if peek() is not None:
        raise UsageError(f"unexpected token in marker expression: {peek()!r}")
    return result


def marker_names(marks: Iterable[Mark]) -> set[str]:
    return {mark_obj.name for mark_obj in marks}


def first_mark(marks: Iterable[Mark], name: str) -> Mark | None:
    for mark_obj in marks:
        if mark_obj.name == name:
            return mark_obj
    return None
