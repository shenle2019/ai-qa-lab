"""OpenAPI / Swagger parsing: turn a spec document into flat endpoint rows."""

from __future__ import annotations

import json
from typing import Any

try:  # PyYAML is optional; JSON specs keep working without it
    import yaml
except ImportError:  # pragma: no cover - depends on environment
    yaml = None

HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")


class SpecError(ValueError):
    """Raised when the document is not a usable OpenAPI/Swagger spec."""


def load_spec(text: str) -> dict[str, Any]:
    """Parse JSON first, then YAML."""
    text = (text or "").strip()
    if not text:
        raise SpecError("spec 内容为空")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        if yaml is None:
            raise SpecError("这份文档不是 JSON，且当前环境没有安装 PyYAML，无法解析 YAML")
        try:
            data = yaml.safe_load(text)
        except Exception as exc:  # noqa: BLE001 - surface the parser message
            raise SpecError(f"无法解析文档：{exc}") from exc
    if not isinstance(data, dict):
        raise SpecError("spec 顶层必须是对象")
    if not ("openapi" in data or "swagger" in data):
        raise SpecError("缺少 openapi/swagger 版本字段，看起来不是 OpenAPI 文档")
    if not isinstance(data.get("paths"), dict) or not data["paths"]:
        raise SpecError("spec 里没有 paths")
    return data


def _resolve(spec: dict[str, Any], node: Any, depth: int = 0) -> Any:
    """Resolve a single-level ``$ref`` (components/schemas or definitions)."""
    if depth > 5 or not isinstance(node, dict):
        return node
    ref = node.get("$ref")
    if not isinstance(ref, str):
        return node
    parts = [p for p in ref.lstrip("#/").split("/") if p]
    target: Any = spec
    for part in parts:
        if not isinstance(target, dict) or part not in target:
            return node
        target = target[part]
    return _resolve(spec, target, depth + 1)


def _type_of(schema: dict[str, Any]) -> str:
    if not isinstance(schema, dict):
        return "string"
    if schema.get("type"):
        return str(schema["type"])
    for key in ("oneOf", "anyOf", "allOf"):
        items = schema.get(key)
        if isinstance(items, list) and items:
            return _type_of(_resolve({}, items[0]))
    return "string"


def _flatten_schema(spec: dict[str, Any], schema: Any, prefix: str = "") -> list[dict[str, Any]]:
    """Flatten an object schema into ``{name, type, required, description}`` rows."""
    schema = _resolve(spec, schema or {})
    if not isinstance(schema, dict):
        return []
    props = schema.get("properties")
    if not isinstance(props, dict):
        return []
    required = set(schema.get("required") or [])
    rows: list[dict[str, Any]] = []
    for name, raw in props.items():
        item = _resolve(spec, raw)
        field = f"{prefix}{name}"
        listed = _type_of(item)
        rows.append(
            {
                "name": field,
                "type": listed,
                "required": name in required,
                "description": (item or {}).get("description") or "",
                "example": (item or {}).get("example"),
            }
        )
        if listed == "object" and prefix.count(".") < 2:
            rows.extend(_flatten_schema(spec, item, prefix=f"{field}."))
        elif listed == "array":
            inner = _resolve(spec, (item or {}).get("items") or {})
            if _type_of(inner) == "object" and prefix.count(".") < 2:
                rows.extend(_flatten_schema(spec, inner, prefix=f"{field}[]."))
    return rows


def _collect_params(spec: dict[str, Any], path_item: dict[str, Any], operation: dict[str, Any]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for source in (
        path_item.get("parameters") or [],
        operation.get("parameters") or [],
    ):
        for raw in source:
            param = _resolve(spec, raw)
            if not isinstance(param, dict) or not param.get("name"):
                continue
            key = (str(param.get("name")), str(param.get("in") or "query"))
            if key in seen:
                continue
            seen.add(key)
            schema = _resolve(spec, param.get("schema") or param)
            merged.append(
                {
                    "name": str(param["name"]),
                    "in": str(param.get("in") or "query"),
                    "required": bool(param.get("required")),
                    "type": _type_of(schema),
                    "description": param.get("description") or "",
                    "example": param.get("example", (schema or {}).get("example")),
                }
            )
    return merged


def _collect_body(spec: dict[str, Any], operation: dict[str, Any]) -> dict[str, Any]:
    body = _resolve(spec, operation.get("requestBody") or {})
    content = (body or {}).get("content")
    if isinstance(content, dict) and content:
        for mime in ("application/json", "application/x-www-form-urlencoded", "multipart/form-data"):
            if mime in content:
                schema = (content[mime] or {}).get("schema")
                return {"content_type": mime, "fields": _flatten_schema(spec, schema)}
        first = next(iter(content.values()))
        return {
            "content_type": "application/json",
            "fields": _flatten_schema(spec, (first or {}).get("schema")),
        }
    # Swagger 2.0 style: body parameter
    for raw in operation.get("parameters") or []:
        param = _resolve(spec, raw)
        if isinstance(param, dict) and param.get("in") == "body":
            return {"content_type": "application/json", "fields": _flatten_schema(spec, param.get("schema"))}
    return {"content_type": "application/json", "fields": []}


def _base_url(spec: dict[str, Any]) -> str | None:
    servers = spec.get("servers")
    if isinstance(servers, list) and servers:
        url = (servers[0] or {}).get("url")
        if isinstance(url, str) and url:
            return url.rstrip("/")
    host = spec.get("host")
    if isinstance(host, str) and host:
        schemes = spec.get("schemes") or ["https"]
        scheme = schemes[0] if isinstance(schemes, list) and schemes else "https"
        base_path = spec.get("basePath") or ""
        return f"{scheme}://{host}{base_path}".rstrip("/")
    return None


def parse_endpoints(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Return endpoint rows ready to be persisted."""
    rows: list[dict[str, Any]] = []
    for path, path_item in (spec.get("paths") or {}).items():
        path_item = _resolve(spec, path_item)
        if not isinstance(path_item, dict):
            continue
        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not isinstance(operation, dict):
                continue
            tags = operation.get("tags") or path_item.get("tags") or []
            module = str(tags[0]) if isinstance(tags, list) and tags else "未分组"
            name = (
                operation.get("summary")
                or operation.get("operationId")
                or f"{method.upper()} {path}"
            )
            responses = []
            for code, raw in (operation.get("responses") or {}).items():
                item = _resolve(spec, raw)
                schema = None
                content = (item or {}).get("content") or {}
                if isinstance(content, dict):
                    for mime in ("application/json", "application/*+json"):
                        if mime in content:
                            schema = _resolve(spec, (content[mime] or {}).get("schema"))
                            break
                if schema is None:
                    schema = _resolve(spec, (item or {}).get("schema"))
                responses.append(
                    {
                        "code": str(code),
                        "description": (item or {}).get("description") or "",
                        "fields": _flatten_schema(spec, schema) if schema else [],
                    }
                )
            rows.append(
                {
                    "method": method.upper(),
                    "path": str(path),
                    "name": str(name)[:200],
                    "module": module[:80],
                    "summary": operation.get("description") or operation.get("summary") or "",
                    "params": _collect_params(spec, path_item, operation),
                    "body": _collect_body(spec, operation),
                    "responses": responses,
                }
            )
    if not rows:
        raise SpecError("spec 的 paths 里没有解析到任何接口")
    return rows


def spec_meta(spec: dict[str, Any]) -> dict[str, Any]:
    info = spec.get("info") or {}
    version = spec.get("openapi") or spec.get("swagger") or ""
    return {
        "title": str(info.get("title") or "未命名接口文档")[:200],
        "version": str(version)[:40],
        "base_url": _base_url(spec),
    }
