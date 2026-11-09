import shutil
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORDLIST_DIR = ROOT / "wordlists"

COMMON_URL = (
    "https://raw.githubusercontent.com/danielmiessler/SecLists/"
    "refs/heads/master/Passwords/Common-Credentials/10k-most-common.txt"
)
COMMON_PATH = WORDLIST_DIR / "10k-most-common.txt"

ROCKYOU_URL = (
    "https://github.com/josuamarcelc/common-password-list/"
    "raw/refs/heads/main/rockyou.txt/rockyou.txt.zip"
)
ROCKYOU_ZIP = WORDLIST_DIR / "rockyou.zip"
ROCKYOU_PATH = WORDLIST_DIR / "rockyou.txt"

WORDLIST_PATH = ROOT / "passwords.txt"


def _download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    try:
        urllib.request.urlretrieve(url, temporary)
        temporary.replace(path)
    except Exception as exc:
        if temporary.exists():
            temporary.unlink()
        raise SystemExit(f"Could not download {path.name}: {exc}") from exc


def _ensure_download(url: str, path: Path, label: str) -> None:
    if path.is_file() and path.stat().st_size > 0:
        print(f"{label} already exists: {path}")
        return
    print(f"Downloading {label} to {path} ...")
    _download(url, path)
    print("Download complete.")


def _ensure_rockyou() -> None:
    if ROCKYOU_PATH.is_file() and ROCKYOU_PATH.stat().st_size > 0:
        print(f"RockYou list already exists: {ROCKYOU_PATH}")
        return

    _ensure_download(ROCKYOU_URL, ROCKYOU_ZIP, "RockYou zip")
    print(f"Extracting rockyou.txt to {ROCKYOU_PATH} ...")
    try:
        with zipfile.ZipFile(ROCKYOU_ZIP) as archive:
            member = next(
                (
                    name
                    for name in archive.namelist()
                    if Path(name).name.lower() == "rockyou.txt"
                ),
                None,
            )
            if member is None:
                raise SystemExit("The RockYou zip does not contain rockyou.txt")
            with archive.open(member) as source, ROCKYOU_PATH.open("wb") as target:
                shutil.copyfileobj(source, target)
    except (zipfile.BadZipFile, OSError) as exc:
        if ROCKYOU_PATH.exists():
            ROCKYOU_PATH.unlink()
        raise SystemExit(f"Could not extract rockyou.txt: {exc}") from exc
    print("Extraction complete.")


def _combine_wordlists(sources: list[Path], destination: Path) -> Path:
    newest_source = max(source.stat().st_mtime for source in sources)
    if (
        destination.is_file()
        and destination.stat().st_size > 0
        and destination.stat().st_mtime >= newest_source
    ):
        print(f"Password list already exists: {destination}")
        return destination

    print("Combining the common list and RockYou into passwords.txt ...")
    temporary = destination.with_suffix(".tmp")
    with temporary.open("wb") as output:
        for source in sources:
            with source.open("rb") as handle:
                shutil.copyfileobj(handle, output)
            output.write(b"\n")
    temporary.replace(destination)
    print("Wordlists combined.")
    return destination


def ensure_password_list() -> Path:
    """Download both lists, extract RockYou, and return the combined file."""
    _ensure_download(COMMON_URL, COMMON_PATH, "common password list")
    _ensure_rockyou()
    return _combine_wordlists([COMMON_PATH, ROCKYOU_PATH], WORDLIST_PATH)


def _ready(path: Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def _ask(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:
        print("No answer was entered. Run H CRACKER from PowerShell or bash and answer the prompts.")
        raise SystemExit(1) from None


def normalize_wordlist_path(text: str) -> Path:
    """Accept a path pasted from PowerShell or bash, including surrounding quotes."""
    cleaned = text.strip()
    if cleaned.startswith("&"):
        cleaned = cleaned[1:].strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
        cleaned = cleaned[1:-1]
    return Path(cleaned).expanduser()


def _ask_for_own_wordlist() -> Path:
    print("Enter the full path to a wordlist file.")
    print("PowerShell and bash: quotes are optional unless the path contains spaces.")
    while True:
        raw = _ask("Wordlist path: ")
        if not raw.strip():
            print("Type a file path, or choose another option with Ctrl+C and start again.")
            continue
        path = normalize_wordlist_path(raw)
        if path.is_dir():
            print(f"That path is a folder, not a wordlist file: {path}")
            continue
        if not path.is_file():
            print(f"Could not find that file: {path}")
            print("Check the spelling, or paste the full path.")
            continue
        if path.stat().st_size == 0:
            print(f"That file is empty: {path}")
            continue
        print(f"Using wordlist: {path}")
        return path


def choose_wordlist() -> Path:
    """Use both local lists, or ask the user to download lists or supply a path."""
    has_common = _ready(COMMON_PATH)
    has_rockyou = _ready(ROCKYOU_PATH)
    if has_common and has_rockyou:
        return _combine_wordlists([COMMON_PATH, ROCKYOU_PATH], WORDLIST_PATH)

    print("Both wordlists are not on this computer yet.")
    print(f"  Common list: {'found' if has_common else 'missing'}")
    print(f"  RockYou:     {'found' if has_rockyou else 'missing'}")
    print()
    print("What do you want to use?")
    print("  1) Download both")
    print("  2) Download only the common list")
    print("  3) Download only RockYou")
    print("  4) Enter a path to your own wordlist")

    while True:
        choice = _ask("Choice [1/2/3/4]: ").strip().lower()
        if choice in {"1", "both"}:
            return ensure_password_list()
        if choice in {"2", "common"}:
            _ensure_download(COMMON_URL, COMMON_PATH, "common password list")
            return COMMON_PATH
        if choice in {"3", "rockyou"}:
            _ensure_rockyou()
            return ROCKYOU_PATH
        if choice in {"4", "path", "own"}:
            return _ask_for_own_wordlist()
        print("Enter 1, 2, 3, or 4.")
