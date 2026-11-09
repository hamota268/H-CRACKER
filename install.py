#!/usr/bin/env python3
"""Check the H CRACKER runtime and install third-party packages when needed."""

import importlib
import platform
import subprocess
import sys
from pathlib import Path

PROJECT_NAME = "H CRACKER"
MIN_PYTHON = (3, 10)
STDLIB_MODULES = (
    "hashlib",
    "mmap",
    "shutil",
    "struct",
    "urllib.request",
    "zipfile",
)
REQUIREMENTS = Path(__file__).resolve().parent / "requirements.txt"


def _requirement_names(path: Path) -> list[str]:
    if not path.is_file():
        return []
    names = []
    for line in path.read_text(encoding="utf-8").splitlines():
        package = line.split("#", 1)[0].strip()
        if package:
            names.append(package)
    return names


def _run_hint() -> str:
    if platform.system() == "Windows":
        return (
            "From PowerShell, run: py -3 main.py\n"
            "If Python is missing, install it from https://www.python.org/downloads/ "
            'and turn on "Add python.exe to PATH".'
        )
    return (
        "From bash, run: python3 main.py\n"
        "If Python is missing: sudo apt install python3 python3-pip\n"
        "or: sudo dnf install python3 python3-pip"
    )


def _pip_hint() -> str:
    if platform.system() == "Windows":
        return (
            "pip could not install the packages.\n"
            "Try PowerShell: py -3 -m ensurepip\n"
            "Then: py -3 -m pip install -r requirements.txt"
        )
    return (
        "pip could not install the packages.\n"
        "Try bash: python3 -m ensurepip --upgrade\n"
        "or install the OS package python3-pip, then:\n"
        "python3 -m pip install --user -r requirements.txt"
    )


def ensure_environment(verbose: bool | None = None) -> bool:
    """Return True when this Python can run H CRACKER."""
    if verbose is None:
        verbose = __name__ == "__main__"

    version = platform.python_version()
    system = platform.system() or "unknown system"
    problems: list[str] = []

    if verbose:
        print(f"{PROJECT_NAME} setup")
        print(f"Interpreter: {sys.executable}")
        print(f"Python {version} on {system} {platform.release()} ({platform.machine()})")
    else:
        print(f"{PROJECT_NAME} setup: Python {version} on {system}")

    if sys.version_info < MIN_PYTHON:
        needed = ".".join(str(part) for part in MIN_PYTHON)
        problems.append(
            f"Python {needed} or newer is required. This interpreter is Python {version}."
        )

    if verbose:
        print("Checking standard library modules:")
    for name in STDLIB_MODULES:
        try:
            importlib.import_module(name)
        except Exception as exc:
            problems.append(f"Standard module {name} failed to import: {exc}")
            if verbose:
                print(f"  {name}: failed")
        else:
            if verbose:
                print(f"  {name}: ok")

    packages = _requirement_names(REQUIREMENTS)
    if not packages:
        print("Third-party packages: none required.")
    else:
        print("Installing third-party packages: " + ", ".join(packages))
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)],
                capture_output=True,
                text=True,
            )
        except OSError as exc:
            problems.append(f"Could not start pip: {exc}")
        else:
            if result.returncode != 0:
                if result.stdout.strip():
                    print(result.stdout.strip())
                if result.stderr.strip():
                    print(result.stderr.strip())
                problems.append(
                    f"pip exited with status {result.returncode}. {_pip_hint()}"
                )
            elif verbose and result.stdout.strip():
                print(result.stdout.strip())

    if problems:
        print("Setup failed.")
        for problem in problems:
            print(f"- {problem}")
        print(_run_hint())
        return False

    print("Setup complete.")
    return True


if __name__ == "__main__":
    sys.exit(0 if ensure_environment() else 1)
