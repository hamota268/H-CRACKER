import hashlib
import mmap
import struct
from pathlib import Path

# Digest bytes, then an 8-byte wordlist offset and a 4-byte password length.
DIGEST_SIZES = {
    "md5": 16,
    "sha1": 20,
    "sha256": 32,
}

HASH_ALGORITHMS = {
    32: "md5",
    40: "sha1",
    64: "sha256",
}


def _record_struct(algorithm: str) -> struct.Struct:
    return struct.Struct(f">{DIGEST_SIZES[algorithm]}sQI")


def index_path_for(wordlist: Path, algorithm: str) -> Path:
    return wordlist.with_name(f"{wordlist.stem}.{algorithm}.idx")


def _index_is_fresh(wordlist: Path, index_path: Path, record_size: int) -> bool:
    return (
        index_path.is_file()
        and index_path.stat().st_size >= record_size
        and index_path.stat().st_size % record_size == 0
        and index_path.stat().st_mtime >= wordlist.stat().st_mtime
    )


def build_index(wordlist: Path, index_path: Path, algorithm: str) -> int:
    """Hash the wordlist once and store the digests in sorted order."""
    record = _record_struct(algorithm)
    packed = []
    with wordlist.open("rb") as source:
        while True:
            line_offset = source.tell()
            line = source.readline()
            if not line:
                break
            password = line.strip()
            if not password:
                continue
            digest = hashlib.new(algorithm, password).digest()
            password_offset = line_offset + line.find(password)
            packed.append(record.pack(digest, password_offset, len(password)))

    packed.sort()
    with index_path.open("wb") as index_file:
        index_file.writelines(packed)
    return len(packed)


def ensure_index(wordlist: Path, algorithm: str) -> Path:
    """Return a sorted index, building it when the wordlist is new."""
    index_path = index_path_for(wordlist, algorithm)
    record_size = _record_struct(algorithm).size
    if _index_is_fresh(wordlist, index_path, record_size):
        return index_path

    print(f"Building a sorted {algorithm.upper()} index...")
    count = build_index(wordlist, index_path, algorithm)
    print(f"Indexed {count} passwords.")
    return index_path


def find_password(
    index_path: Path,
    wordlist: Path,
    digest: bytes,
    algorithm: str,
) -> str | None:
    """Binary-search the sorted index and read only the matching password."""
    record = _record_struct(algorithm)
    count = index_path.stat().st_size // record.size
    if count == 0:
        return None

    with index_path.open("rb") as index_file, wordlist.open("rb") as word_file:
        with mmap.mmap(index_file.fileno(), 0, access=mmap.ACCESS_READ) as index:
            low = 0
            high = count - 1
            while low <= high:
                mid = (low + high) // 2
                stored, offset, length = record.unpack_from(index, mid * record.size)
                if stored == digest:
                    word_file.seek(offset)
                    return word_file.read(length).decode("utf-8", errors="replace")
                if stored < digest:
                    low = mid + 1
                else:
                    high = mid - 1
    return None
