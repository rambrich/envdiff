"""Parser for .env files."""

from pathlib import Path
from typing import Dict, Optional


def parse_env_file(filepath: str | Path) -> Dict[str, Optional[str]]:
    """
    Parse a .env file and return a dictionary of key-value pairs.

    Supports:
    - KEY=VALUE
    - KEY="VALUE" or KEY='VALUE' (quotes stripped)
    - Comments starting with #
    - Empty lines (ignored)
    - Keys with no value (KEY= or just KEY)

    Args:
        filepath: Path to the .env file.

    Returns:
        Dictionary mapping keys to their values (or None if no value).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f".env file not found: {filepath}")

    env_vars: Dict[str, Optional[str]] = {}

    with filepath.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()

                # Strip surrounding quotes
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]

                env_vars[key] = value if value else None
            else:
                # Key with no equals sign
                env_vars[line.strip()] = None

    return env_vars
