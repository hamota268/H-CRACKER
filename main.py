#!/usr/bin/env python3
"""H CRACKER command-line hash lookup."""

import sys
import time

from hash_index import HASH_ALGORITHMS, ensure_index, find_password
from install import ensure_environment
from password_list import choose_wordlist

BANNER = r"""
 _   _     ____ ____      _    ____ _  _______ ____
| | | |   / ___|  _ \    / \  / ___| |/ / ____|  _ \
| |_| |  | |   | |_) |  / _ \| |   | ' /|  _| | |_) |
|  _  |  | |___|  _ <  / ___ \ |___| . \| |___|  _ <
|_| |_|   \____|_| \_\/_/   \_\____|_|\_\_____|_| \_\
                     H CRACKER
""".strip("\n")


def main() -> None:
    print(BANNER)
    print()
    if not ensure_environment():
        raise SystemExit(1)
    print()

    wordlist = choose_wordlist()
    user_hash = input("Enter an MD5, SHA1, or SHA256 hash: ").strip().lower()
    if len(user_hash) not in HASH_ALGORITHMS or any(
        character not in "0123456789abcdef" for character in user_hash
    ):
        print("Enter a hexadecimal MD5 (32), SHA1 (40), or SHA256 (64) hash.")
        return

    algorithm = HASH_ALGORITHMS[len(user_hash)]
    index_path = ensure_index(wordlist, algorithm)

    started = time.perf_counter()
    password = find_password(
        index_path,
        wordlist,
        bytes.fromhex(user_hash),
        algorithm,
    )
    elapsed = time.perf_counter() - started

    if password is None:
        print("Password not found")
    else:
        print(f"Password found: {password}")
    print(f"{algorithm.upper()} search took {elapsed:.6f} seconds.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(130)
