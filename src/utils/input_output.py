import json
from pathlib import Path
from typing import Any


def save_json(payload: Any, output_path: Path) -> None:
    """
    Saves a Python object to a JSON file under the specified path, ensuring that the parent directories exist.
    If the file already exists, it will be overwritten and all parent directories will be created if they do not exist.
    :param payload: the data to be saved, which can be any JSON-serializable Python object (e.g., dict, list).
    :param output_path: the file path where the JSON data should be saved.
    :return: None
    """
    # Check if the output file has a .json extension
    if output_path.suffix.lower() != ".json":
        raise ValueError(f"Output path must point to a .json file: {output_path}")

    # Create parent directories if they do not exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Serialize the payload to a JSON string
        serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    except TypeError as exc:
        raise TypeError(f"Payload is not JSON-serializable: {output_path}") from exc

    try:
        # Write serialized JSON to the output file
        output_path.write_text(serialized, encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Unable to write JSON file: {output_path}") from exc


def load_json(input_path: Path) -> Any:
    """
    Loads a JSON file from the specified path and returns its content as a Python object.
    :param input_path: the file path from which to load the JSON data.
    :return: the content of the JSON file as a Python object (e.g., dict, list).
    """
    # Check if the file input file has a .json extension
    if input_path.suffix.lower() != ".json":
        raise ValueError(f"Input path must point to a .json file: {input_path}")

    # Check if the file exists
    if not input_path.exists():
        raise FileNotFoundError(f"JSON file not found: {input_path}")

    # Check if the path is a file (not a directory)
    if not input_path.is_file():
        raise ValueError(f"Input path is not a file: {input_path}")

    try:
        content = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Unable to read JSON file: {input_path}") from exc

    if not content.strip():
        raise ValueError(f"JSON file is empty: {input_path}")

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise json.JSONDecodeError(
            f"Invalid JSON in file: {input_path}",
            exc.doc,
            exc.pos,
        ) from exc