"""Fixture decorator and a small dependency-injection engine."""

from __future__ import annotations

import inspect
import time
from pathlib import Path
from typing import Any, Callable

from .errors import FixtureError, FixtureNotFound, Skipped
from .model import Case, Failure, FixtureDef, FixtureTiming


def fixture(
    func: Callable[..., Any] | None = None,
    *,
    scope: str = "function",
    autouse: bool = False,
    name: str | None = None,
) -> Any:
    if scope not in {"function", "module", "session"}:
        raise ValueError(f"unsupported fixture scope: {scope}")

    def decorate(target: Callable[..., Any]) -> Callable[..., Any]:
        setattr(target, "__minipytest_fixture_scope__", scope)
        setattr(target, "__minipytest_fixture_autouse__", autouse)
        if name:
            setattr(target, "__minipytest_fixture_name__", name)
        return target

    if func is not None:
        return decorate(func)
    return decorate


def _failure_from_exception(exc: BaseException, phase: str) -> Failure:
    import traceback

    return Failure(
        message=str(exc) or exc.__class__.__name__,
        phase=phase,
        type=exc.__class__.__name__,
        traceback="".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
    )


class FixtureManager:
    """Run-level fixture cache with function/module/session scopes."""

    def __init__(self) -> None:
        self.session_cache: dict[tuple[str, str], Any] = {}
        self.module_cache: dict[tuple[str, str], Any] = {}
        self.function_cache: dict[tuple[str, str], Any] = {}
        self.session_finalizers: list[tuple[str, str, str, Any]] = []
        self.module_finalizers: list[tuple[str, str, str, Any]] = []
        self.function_finalizers: list[tuple[str, str, str, Any]] = []
        self.defs: dict[str, FixtureDef] = {}
        self.case_params: dict[str, Any] = {}
        self.module_key: Path | None = None
        self.case_timings: list[FixtureTiming] = []
        self.run_finalization_errors: list[Failure] = []
        self._resolving: set[tuple[str, str]] = set()

    def begin_case(self, case: Case, module_key: Path) -> None:
        if self.module_key != module_key:
            self.finalize_module()
            self.module_cache.clear()
            self.module_key = module_key
        self.defs = {defn.name: defn for defn in case.fixtures}
        self.case_params = dict(case.params)
        self.reset_function()

    def reset_function(self) -> None:
        self.function_cache.clear()
        self.function_finalizers.clear()
        self.case_timings = []

    def _cache_for(self, defn: FixtureDef) -> dict[tuple[str, str], Any]:
        if defn.scope == "function":
            return self.function_cache
        if defn.scope == "module":
            return self.module_cache
        return self.session_cache

    def _finalizers_for(self, defn: FixtureDef) -> list[tuple[str, str, str, Any]]:
        if defn.scope == "function":
            return self.function_finalizers
        if defn.scope == "module":
            return self.module_finalizers
        return self.session_finalizers

    def resolve(self, name: str) -> Any:
        if name in self.case_params:
            return self.case_params[name]

        defn = self.defs.get(name)
        if defn is None:
            raise FixtureNotFound(name)

        key = (defn.name, defn.source)
        cache = self._cache_for(defn)
        if key in cache:
            return cache[key]
        if key in self._resolving:
            raise FixtureError(defn.name, "setup", RuntimeError("circular fixture dependency"))

        self._resolving.add(key)
        start = time.perf_counter()
        try:
            signature = inspect.signature(defn.func)
            kwargs: dict[str, Any] = {}
            for param_name, param in signature.parameters.items():
                if param_name in self.case_params:
                    kwargs[param_name] = self.case_params[param_name]
                elif param_name in self.defs:
                    kwargs[param_name] = self.resolve(param_name)
                elif param.default is not inspect.Parameter.empty:
                    continue
                else:
                    raise FixtureNotFound(param_name)

            produced = defn.func(**kwargs)
            value = produced
            if inspect.isgenerator(produced):
                try:
                    value = next(produced)
                except StopIteration as exc:
                    raise FixtureError(defn.name, "setup", RuntimeError("fixture did not yield")) from exc
                self._finalizers_for(defn).append((defn.name, defn.source, defn.scope, produced))

            cache[key] = value
            self.case_timings.append(
                FixtureTiming(defn.name, defn.scope, "setup", (time.perf_counter() - start) * 1000)
            )
            return value
        except Skipped:
            raise
        except FixtureError:
            raise
        except Exception as exc:
            self.case_timings.append(
                FixtureTiming(defn.name, defn.scope, "setup", (time.perf_counter() - start) * 1000, "error")
            )
            raise FixtureError(defn.name, "setup", exc) from exc
        finally:
            self._resolving.discard(key)

    def setup_autouse(self) -> None:
        for defn in self.defs.values():
            if defn.autouse:
                self.resolve(defn.name)

    def resolve_test_params(self, func: Callable[..., Any], case: Case, drop_self: bool = False) -> dict[str, Any]:
        signature = inspect.signature(func)
        kwargs: dict[str, Any] = {}
        for index, (param_name, param) in enumerate(signature.parameters.items()):
            if drop_self and index == 0 and param_name == "self":
                continue
            if param_name in case.params:
                kwargs[param_name] = case.params[param_name]
            elif param_name in self.defs:
                kwargs[param_name] = self.resolve(param_name)
            elif param.default is not inspect.Parameter.empty:
                continue
            else:
                raise FixtureNotFound(param_name)
        return kwargs

    def _finalize(self, finalizers: list[tuple[str, str, str, Any]], phase: str) -> list[Failure]:
        errors: list[Failure] = []
        while finalizers:
            name, _source, scope, generator = finalizers.pop()
            start = time.perf_counter()
            try:
                next(generator)
            except StopIteration:
                pass
            except Exception as exc:
                errors.append(_failure_from_exception(exc, phase))
                self.case_timings.append(
                    FixtureTiming(name, scope, "teardown", (time.perf_counter() - start) * 1000, "error")
                )
            else:
                self.case_timings.append(
                    FixtureTiming(name, scope, "teardown", (time.perf_counter() - start) * 1000)
                )
        return errors

    def finalize_function(self) -> list[Failure]:
        return self._finalize(self.function_finalizers, "teardown")

    def finalize_module(self) -> None:
        self.run_finalization_errors.extend(self._finalize(self.module_finalizers, "teardown"))

    def finalize_session(self) -> None:
        self.run_finalization_errors.extend(self._finalize(self.session_finalizers, "teardown"))


__all__ = ["fixture", "FixtureManager"]
