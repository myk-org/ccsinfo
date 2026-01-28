"""Base model with orjson support."""

from typing import Any

import orjson
from pydantic import BaseModel, ConfigDict


def orjson_dumps(v: Any, *, default: Any) -> str:
    """Serialize to JSON using orjson."""
    result: bytes = orjson.dumps(v, default=default)
    return result.decode()


def orjson_loads(v: str | bytes) -> Any:
    """Deserialize from JSON using orjson."""
    return orjson.loads(v)


class BaseORJSONModel(BaseModel):
    """Base model with orjson serialization support."""

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        arbitrary_types_allowed=True,
    )
