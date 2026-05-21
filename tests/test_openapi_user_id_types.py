from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from aiograpi_rest.main import app


def _user_id_schemas(openapi: dict[str, Any]) -> Iterator[tuple[str, str, str, dict[str, Any]]]:
    for path, methods in openapi["paths"].items():
        for method, operation in methods.items():
            if method == "parameters":
                continue
            operation_id = f"{method.upper()} {path}"
            for parameter in operation.get("parameters", []):
                name = parameter["name"]
                if name in {"user_id", "user_ids"}:
                    yield operation_id, name, parameter["in"], parameter["schema"]

            for content in operation.get("requestBody", {}).get("content", {}).values():
                schema = content.get("schema", {})
                if "$ref" in schema:
                    schema_name = schema["$ref"].rsplit("/", 1)[-1]
                    schema = openapi["components"]["schemas"][schema_name]
                for name, property_schema in schema.get("properties", {}).items():
                    if name in {"user_id", "user_ids"}:
                        yield operation_id, name, "body", property_schema


def test_openapi_declares_instagram_user_ids_as_strings():
    errors = []

    for operation_id, name, location, schema in _user_id_schemas(app.openapi()):
        if name == "user_id" and schema.get("type") != "string":
            errors.append(f"{operation_id} {location}.{name}: {schema!r}")
        if name == "user_ids":
            item_schema = schema.get("items", {})
            if schema.get("type") != "array" or item_schema.get("type") != "string":
                errors.append(f"{operation_id} {location}.{name}: {schema!r}")

    assert errors == []
