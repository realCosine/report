from pathlib import Path


def parse_posix_paths(data):
    """
    Recursively parses a dictionary or list to convert PosixPath objects to strings.
    """
    if isinstance(data, dict):
        return {str(k): parse_posix_paths(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [parse_posix_paths(item) for item in data]
    elif isinstance(data, Path):
        return str(data)
    else:
        return data
