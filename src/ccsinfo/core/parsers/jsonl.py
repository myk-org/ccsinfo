"""Generic JSONL and JSON parser utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar, cast

import orjson

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pydantic import BaseModel

T = TypeVar("T", bound="BaseModel")

logger = logging.getLogger(__name__)


def parse_jsonl[T: "BaseModel"](
    file_path: Path,
    model: type[T] | None = None,
    *,
    skip_malformed: bool = True,
) -> Iterator[T | dict[str, Any]]:
    """Parse a JSONL file, optionally converting to Pydantic models.

    Args:
        file_path: Path to the JSONL file to parse.
        model: Optional Pydantic model class to validate each line against.
        skip_malformed: If True, skip malformed lines and log a warning.
                       If False, raise an exception on malformed lines.

    Yields:
        Parsed data as either a Pydantic model instance or a dict.

    Raises:
        FileNotFoundError: If the file does not exist.
        orjson.JSONDecodeError: If skip_malformed is False and a line is invalid JSON.
        pydantic.ValidationError: If skip_malformed is False and validation fails.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"JSONL file not found: {file_path}")

    with file_path.open("rb") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                data = orjson.loads(line)
            except orjson.JSONDecodeError as e:
                if skip_malformed:
                    logger.warning(
                        "Skipping malformed JSON at line %d in %s: %s",
                        line_num,
                        file_path,
                        e,
                    )
                    continue
                raise

            if model is not None:
                try:
                    yield model.model_validate(data)
                except Exception as e:
                    if skip_malformed:
                        logger.warning(
                            "Skipping invalid data at line %d in %s: %s",
                            line_num,
                            file_path,
                            e,
                        )
                        continue
                    raise
            else:
                yield data


def parse_json[T: "BaseModel"](file_path: Path, model: type[T] | None = None) -> T | dict[str, Any]:
    """Parse a JSON file, optionally converting to a Pydantic model.

    Args:
        file_path: Path to the JSON file to parse.
        model: Optional Pydantic model class to validate the data against.

    Returns:
        Parsed data as either a Pydantic model instance or a dict.

    Raises:
        FileNotFoundError: If the file does not exist.
        orjson.JSONDecodeError: If the file contains invalid JSON.
        pydantic.ValidationError: If model validation fails.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    with file_path.open("rb") as f:
        data = orjson.loads(f.read())

    if model is not None:
        result: T = model.model_validate(data)
        return result
    return cast("dict[str, Any]", data)


def parse_json_as[T: "BaseModel"](file_path: Path, model: type[T]) -> T:
    """Parse a JSON file into a Pydantic model.

    This is a type-safe variant of parse_json that always returns the model type.

    Args:
        file_path: Path to the JSON file to parse.
        model: Pydantic model class to validate the data against.

    Returns:
        Parsed data as a Pydantic model instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        orjson.JSONDecodeError: If the file contains invalid JSON.
        pydantic.ValidationError: If model validation fails.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    with file_path.open("rb") as f:
        data = orjson.loads(f.read())

    return model.model_validate(data)


def iter_jsonl_files(
    directory: Path,
    pattern: str = "*.jsonl",
) -> Iterator[Path]:
    """Iterate over JSONL files in a directory.

    Args:
        directory: Directory to search for JSONL files.
        pattern: Glob pattern for matching files.

    Yields:
        Paths to JSONL files.
    """
    if not directory.exists():
        return

    yield from sorted(directory.glob(pattern))


def iter_json_files(
    directory: Path,
    pattern: str = "*.json",
) -> Iterator[Path]:
    """Iterate over JSON files in a directory.

    Args:
        directory: Directory to search for JSON files.
        pattern: Glob pattern for matching files.

    Yields:
        Paths to JSON files.
    """
    if not directory.exists():
        return

    yield from sorted(directory.glob(pattern))
