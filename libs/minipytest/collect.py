"""Test discovery, fixture discovery, and parametrization expansion."""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
import itertools
import re
import sys
import traceback
from pathlib import Path
from typing import Any, Iterable, Sequence

from .markers import Mark, Param, ParametrizeSpec, get_marks
from .model import Case, CollectResult, CollectionError, FixtureDef

IGNORED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".tmp",
    "dist",
    ".reports",
    "htmlcov",
}


def _unique_module_name(prefix: str, path: Path) -> str:
    digest = hashlib.sha1(str(path.resolve()).encode("utf-8")).hexdigest()[:16]
    return f"_minipytest_{prefix}_{digest}"


def _ensure_path(path: Path) -> None:
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)


def _load_module(path: Path, prefix: str) -> Any:
    _ensure_path(path.parent)
    name = _unique_module_name(prefix, path)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


def _iter_test_files(paths: Sequence[str | Path]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for raw in paths:
        path = Path(raw).resolve()
        if path.is_file():
            candidates = [path] if path.name.startswith("test_") and path.suffix == ".py" else []
        elif path.is_dir():
            candidates = sorted(
                p for p in path.rglob("test_*.py") if not any(part in IGNORED_DIRS for part in p.parts)
            )
        else:
            candidates = []
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(resolved)
    return files


def _collect_fixtures(module: Any) -> list[FixtureDef]:
    fixtures: list[FixtureDef] = []
    source = str(getattr(module, "__file__", ""))
    for name, obj in vars(module).items():
        if not inspect.isfunction(obj):
            continue
        scope = getattr(obj, "__minipytest_fixture_scope__", None)
        if scope is None:
            continue
        fixture_name = getattr(obj, "__minipytest_fixture_name__", None) or name
        autouse = bool(getattr(obj, "__minipytest_fixture_autouse__", False))
        fixtures.append(FixtureDef(fixture_name, obj, scope, autouse, source))
    return fixtures


_CONFTEST_CACHE: dict[Path, Any] = {}


def _load_conftests(test_file: Path, rootdir: Path) -> list[FixtureDef]:
    chain: list[Path] = []
    current = test_file.parent
    while True:
        chain.append(current)
        if current == rootdir or current.parent == current:
            break
        current = current.parent
    chain.reverse()

    fixtures: list[FixtureDef] = []
    for directory in chain:
        conftest = directory / "conftest.py"
        if not conftest.exists():
            continue
        resolved = conftest.resolve()
        module = _CONFTEST_CACHE.get(resolved)
        if module is None:
            module = _load_module(resolved, "conftest")
            _CONFTEST_CACHE[resolved] = module
        fixtures.extend(_collect_fixtures(module))
    return fixtures


def _signature(func: Any) -> inspect.Signature:
    return inspect.signature(func)


def _source_line(obj: Any) -> int:
    try:
        return inspect.getsourcelines(obj)[1]
    except (OSError, TypeError):
        return 0


def _param_position(func: Any, name: str) -> int:
    params = list(_signature(func).parameters)
    if name not in params:
        raise ValueError(f"parametrize name {name!r} is not in the test signature")
    return params.index(name)


def _default_id(value: Any) -> str:
    text = str(value).strip()
    text = re.sub(r"\s+", "_", text)
    for char in "[]:/\\":
        text = text.replace(char, "_")
    return (text or "param")[:50]


def _expanded_values(spec: ParametrizeSpec) -> list[tuple[tuple[Any, ...], str, tuple[Mark, ...]]]:
    expanded: list[tuple[tuple[Any, ...], str, tuple[Mark, ...]]] = []
    for index, raw in enumerate(spec.argvalues):
        if isinstance(raw, Param):
            values = raw.values
            custom_id = raw.id
            marks = raw.marks
        elif len(spec.argnames) == 1:
            values = (raw,)
            custom_id = None
            marks = ()
        else:
            if not isinstance(raw, (tuple, list)) or len(raw) != len(spec.argnames):
                raise ValueError(
                    f"parametrize values for {spec.argnames} must be tuples of length {len(spec.argnames)}"
                )
            values = tuple(raw)
            custom_id = None
            marks = ()

        if len(values) != len(spec.argnames):
            raise ValueError(f"parametrize value count does not match {spec.argnames}")

        default_id = "-".join(_default_id(value) for value in values)
        spec_id = spec.ids[index] if spec.ids else None
        expanded.append((values, spec_id or custom_id or default_id, marks))
    return expanded


def _make_cases(
    func: Any,
    path: Path,
    rootdir: Path,
    fixtures: tuple[FixtureDef, ...],
    class_name: str | None = None,
    cls: type | None = None,
    class_marks: tuple[Mark, ...] = (),
) -> list[Case]:
    specs = list(getattr(func, "__minipytest_parametrize__", ()))
    specs.sort(key=lambda spec: _param_position(func, spec.argnames[0]))

    base_name = func.__name__
    try:
        relative = path.relative_to(rootdir).as_posix()
    except ValueError:
        relative = path.as_posix()

    base_node = f"{relative}::{class_name}::{base_name}" if class_name else f"{relative}::{base_name}"
    func_marks = get_marks(func)
    marks = tuple(class_marks) + tuple(func_marks)

    if not specs:
        return [
            Case(
                nodeid=base_node,
                path=path,
                name=base_name,
                func=func,
                params={},
                marks=marks,
                cls=cls,
                class_name=class_name,
                fixtures=fixtures,
            )
        ]

    value_lists = [_expanded_values(spec) for spec in specs]
    cases: list[Case] = []
    used_ids: dict[str, int] = {}

    for combo in itertools.product(*value_lists):
        params: dict[str, Any] = {}
        id_parts: list[str] = []
        extra_marks: list[Mark] = []
        for spec, (values, part_id, value_marks) in zip(specs, combo):
            for name, value in zip(spec.argnames, values):
                params[name] = value
            id_parts.append(part_id)
            extra_marks.extend(value_marks)

        param_id = "-".join(id_parts) if id_parts else ""
        count = used_ids.get(param_id, 0)
        used_ids[param_id] = count + 1
        if count:
            param_id = f"{param_id}_{count}"

        cases.append(
            Case(
                nodeid=f"{base_node}[{param_id}]",
                path=path,
                name=base_name,
                func=func,
                params=params,
                marks=marks + tuple(extra_marks),
                cls=cls,
                class_name=class_name,
                fixtures=fixtures,
                param_id=param_id,
            )
        )
    return cases


def _collect_from_module(
    module: Any,
    path: Path,
    rootdir: Path,
    fixtures: tuple[FixtureDef, ...],
) -> list[Case]:
    cases: list[Case] = []

    functions: list[Any] = []
    classes: list[type] = []
    for name, obj in vars(module).items():
        if inspect.isfunction(obj) and obj.__module__ == module.__name__:
            if name.startswith("test_"):
                functions.append(obj)
        elif inspect.isclass(obj) and obj.__module__ == module.__name__:
            if name.startswith("Test") and obj.__init__ is object.__init__:
                classes.append(obj)

    functions.sort(key=lambda item: item.__code__.co_firstlineno)
    classes.sort(key=_source_line)

    for func in functions:
        if inspect.iscoroutinefunction(func):
            raise ValueError(f"async test is not supported: {func.__name__}")
        cases.extend(_make_cases(func, path, rootdir, fixtures))

    for cls in classes:
        class_marks = get_marks(cls)
        methods = [
            (name, obj)
            for name, obj in vars(cls).items()
            if inspect.isfunction(obj) and name.startswith("test_")
        ]
        methods.sort(key=lambda item: item[1].__code__.co_firstlineno)
        for _, method in methods:
            if inspect.iscoroutinefunction(method):
                raise ValueError(f"async test is not supported: {cls.__name__}.{method.__name__}")
            cases.extend(
                _make_cases(
                    method,
                    path,
                    rootdir,
                    fixtures,
                    class_name=cls.__name__,
                    cls=cls,
                    class_marks=class_marks,
                )
            )
    return cases


def collect(paths: Sequence[str | Path], rootdir: Path) -> CollectResult:
    rootdir = Path(rootdir).resolve()
    result = CollectResult()
    for test_file in _iter_test_files(paths):
        try:
            module = _load_module(test_file, "test")
            conftest_fixtures = _load_conftests(test_file, rootdir)
            module_fixtures = _collect_fixtures(module)

            fixture_map: dict[str, FixtureDef] = {}
            for defn in conftest_fixtures:
                fixture_map[defn.name] = defn
            for defn in module_fixtures:
                fixture_map[defn.name] = defn
            fixtures = tuple(fixture_map.values())

            result.cases.extend(_collect_from_module(module, test_file, rootdir, fixtures))
        except Exception as exc:
            try:
                rel = test_file.relative_to(rootdir).as_posix()
            except ValueError:
                rel = test_file.as_posix()
            result.errors.append(
                CollectionError(
                    path=rel,
                    message=f"{type(exc).__name__}: {exc}",
                    traceback=traceback.format_exc(),
                )
            )
    return result
