"""Locate and load CYRIL's external, non-secret environment configuration.

The configuration file is discovered relative to the application location,
not the current working directory. Secrets remain in the credential provider.
"""

import os
import sys
from pathlib import Path


REQUIRED_SETTINGS = (
    "ALPHAOMEGA_CLIENT_ID",
    "SUPABASE_URL",
    "SUPABASE_PUBLISHABLE_KEY",
    "SUPABASE_ALPHAOMEGA_EMAIL",
)


def find_configuration_file() -> Path:
    """Find config/.env upward from the application, or use an explicit override."""
    override = os.getenv("CYRIL_CONFIG_FILE", "").strip()
    if override:
        candidate = Path(override).expanduser().resolve()
        if not candidate.is_file():
            raise RuntimeError(f"CYRIL_CONFIG_FILE does not point to a file: {candidate}")
        return candidate

    # Frozen applications discover external configuration beside the executable
    # or in an ancestor directory. Never use PyInstaller's temporary extraction.
    starting_directory = (
        Path(sys.executable).resolve().parent
        if getattr(sys, "frozen", False)
        else Path(__file__).resolve().parent
    )
    for directory in (starting_directory, *starting_directory.parents):
        candidate = directory / "config" / ".env"
        if candidate.is_file():
            return candidate

    raise RuntimeError(
        "CYRIL configuration was not found. Expected config/.env in the "
        f"application directory or one of its parents (starting at {starting_directory}). "
        "Alternatively, set CYRIL_CONFIG_FILE to the full configuration file path."
    )


def load_local_configuration() -> Path:
    """Load public settings without replacing values already in the environment."""
    configuration_file = find_configuration_file()
    for line_number, raw_line in enumerate(
        configuration_file.read_text(encoding="utf-8-sig").splitlines(), 1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise RuntimeError(f"Invalid .env entry at line {line_number}.")
        name, value = line.split("=", 1)
        name, value = name.strip(), value.strip()
        if not name.isidentifier():
            raise RuntimeError(f"Invalid .env variable name at line {line_number}.")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ.setdefault(name, value)

    missing = [name for name in REQUIRED_SETTINGS if not os.getenv(name, "").strip()]
    if missing:
        raise RuntimeError(
            "CYRIL configuration is missing: " + ", ".join(missing)
            + f". Add these non-secret settings to {configuration_file}."
        )
    return configuration_file
