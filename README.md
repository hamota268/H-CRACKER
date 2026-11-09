<div align="center">

```
 _   _     ____ ____      _    ____ _  _______ ____
| | | |   / ___|  _ \    / \  / ___| |/ / ____|  _ \
| |_| |  | |   | |_) |  / _ \| |   | ' /|  _| | |_) |
|  _  |  | |___|  _ <  / ___ \ |___| . \| |___|  _ <
|_| |_|   \____|_| \_\/_/   \_\____|_|\_\_____|_| \_\
                     H CRACKER
```

### 🔓 Fast, offline hash lookup from the command line

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-4E9BCD?style=for-the-badge&logo=linux&logoColor=white)](#-requirements)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](#-license)
[![Dependencies](https://img.shields.io/badge/Dependencies-None%20(stdlib)-brightgreen?style=for-the-badge)](#-requirements)

**H CRACKER** is a CLI tool that resolves **MD5**, **SHA1**, and **SHA256** hashes against the two most famous password lists on the internet — the *10k Most Common* list and **RockYou** — using a sorted hash index and binary search. No cloud, no API keys, no waiting on a server. Just you, your terminal, and ~14 million passwords.

</div>

---

## ✨ Highlights

| | Feature |
|---|---|
| ⚡ | **Binary search, not brute hash** — lookups are ~24 comparisons, not 14 million hashes |
| 🧠 | **Auto algorithm detection** — 32 / 40 / 64 hex chars → MD5 / SHA1 / SHA256 |
| 🗂️ | **Memory-mapped index** — the OS pages in only what it needs |
| 📥 | **Auto-downloads wordlists** — Common-10k + full RockYou, extracted from zip |
| 🔁 | **Smart caching** — indices rebuild only when `passwords.txt` changes |
| 🖥️ | **Zero third-party packages** — pure Python 3.10+ standard library |
| 🪟 | **Windows & Linux ready** — install & runtime checks included |
| 🎨 | **The banner** — because every cracker deserves one |

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/h-cracker.git
cd h-cracker
```

### 2. Run it

<table>
<tr><th>Windows (PowerShell)</th><th>Linux / macOS (bash)</th></tr>
<tr>
<td>

```powershell
py -3 main.py
```

</td>
<td>

```bash
python3 main.py
```

</td>
</tr>
</table>

That's it — **no `pip install` required**. If Python 3.10+ is missing, H CRACKER will tell you exactly how to install it.

### 3. Feed it a hash

```
Enter an MD5, SHA1, or SHA256 hash: 9f2feb0f1ef425b292f2f94bc8482494df430413
Password found: love
SHA1 search took 0.000412 seconds.
```

> 🎯 **Fun fact:** the SHA1 hash `9f2feb0f1ef425b292f2f94bc8482494df430413` still resolves to **`love`**.

---

## 🧩 How It Works

```
                    ┌─────────────────────────────┐
  hash input ──────▶│  length → 32 / 40 / 64 hex  │
                    │  → MD5 / SHA1 / SHA256      │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │  passwords.<algo>.idx       │  ◀── built once,
                    │  sorted by raw digest       │      reused until
                    │  record = hash│offset│len   │      passwords.txt changes
                    └──────────────┬──────────────┘
                                   │
                          binary search
                          (≈ log₂ N comparisons)
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │  seek to byte offset in     │
                    │  passwords.txt, read N bytes│  ◀── only ONE line read
                    └─────────────────────────────┘
```

### The index record

Each password becomes a fixed-size record:

| Field | Size | Purpose |
|-------|------|---------|
| `digest` | 16 / 20 / 32 B | the raw hash (MD5 / SHA1 / SHA256) |
| `offset` | 8 B | byte position of the password in `passwords.txt` |
| `length` | 4 B | how many bytes to read back |

Records are **sorted by digest**, then memory-mapped. A lookup walks the sorted array with `low` / `high` bounds:

- 🔍 **match** → seek to `offset`, read `length` bytes, done
- ⬆️ **stored < target** → search upper half
- ⬇️ **stored > target** → search lower half

For the combined **~14 million passwords** the index costs:

| Algorithm | Record size | Index on disk |
|-----------|-------------|---------------|
| MD5 | 28 B | ≈ **390 MB** |
| SHA1 | 32 B | ≈ **450 MB** |
| SHA256 | 44 B | ≈ **615 MB** |

First lookup per algorithm builds the index. Later lookups reuse it — until `passwords.txt` gets a newer mtime, which triggers an automatic rebuild.

---

## 🗂️ Project Layout

```
h-cracker/
├── main.py            # Banner, prompts, algorithm detection, timer
├── hash_index.py      # Record struct, index build, mmap binary search
├── password_list.py   # Wordlist download / extract / merge / prompt
├── install.py         # Python + stdlib runtime check, pip installer
├── requirements.txt   # (empty — stdlib only)
├── passwords.txt      # combined wordlist (generated)
└── wordlists/
    ├── 10k-most-common.txt
    ├── rockyou.zip
    └── rockyou.txt    # extracted from zip
```

---

## 🎛️ Wordlists

On first run, if both lists are present, H CRACKER silently merges them into `passwords.txt`. If either is missing you get a menu:

```
Both wordlists are not on this computer yet.
  Common list: missing
  RockYou:     missing

What do you want to use?
  1) Download both
  2) Download only the common list
  3) Download only RockYou
  4) Enter a path to your own wordlist
```

| Option | What you get |
|--------|--------------|
| **1** | `10k-most-common.txt` + full `rockyou.txt`, merged → `passwords.txt` |
| **2** | Just the 10k common list (fast, tiny index) |
| **3** | Full RockYou (14M passwords, big index, best coverage) |
| **4** | Any file you point at — quotes and `&` from PowerShell are stripped |

Sources:

- **Common list** — [danielmiessler/SecLists](https://github.com/danielmiessler/SecLists) `Passwords/Common-Credentials/10k-most-common.txt`
- **RockYou** — [`josuamarcelc/common-password-list`](https://github.com/josuamarcelc/common-password-list) (`rockyou.txt.zip`, auto-extracted)

---

## 🧪 Example Session

```
$ python3 main.py

 _   _     ____ ____      _    ____ _  _______ ____
| | | |   / ___|  _ \    / \  / ___| |/ / ____|  _ \
| |_| |  | |   | |_) |  / _ \| |   | ' /|  _| | |_) |
|  _  |  | |___|  _ <  / ___ \ |___| . \| |___|  _ <
|_| |_|   \____|_| \_\/_/   \_\____|_|\_\_____|_| \_\

H CRACKER setup: Python 3.12.3 on Linux
  hashlib: ok   mmap: ok   struct: ok   ...
Setup complete.

Building a sorted SHA1 index...
Indexed 14231520 passwords.
Enter an MD5, SHA1, or SHA256 hash: 9f2feb0f1ef425b292f2f94bc8482494df430413
Password found: love
SHA1 search took 0.000198 seconds.
```

---

## 🧰 Requirements

| | |
|---|---|
| 🐍 **Python** | **3.10+** (uses `str \| None` union syntax) |
| 📦 **Packages** | **None** — everything is standard library |
| 💾 **Disk** | ≈ 140 MB for `rockyou.txt`, up to ≈ 615 MB per SHA256 index |
| 🧠 **RAM** | Modest — the index is memory-mapped, not read into memory |

`install.py` runs on every startup and:

1. Verifies the Python version is ≥ 3.10
2. Imports each required stdlib module (`hashlib`, `mmap`, `struct`, …)
3. Runs `pip install -r requirements.txt` only if that file lists anything
4. Prints OS-specific fix hints when something fails

---

## ⚙️ Customizing

**Add a hash algorithm** — extend the two dicts in `hash_index.py`:

```python
DIGEST_SIZES = {
    "md5": 16, "sha1": 20, "sha256": 32,
    "sha512": 64,                    # ← new
}

HASH_ALGORITHMS = {
    32: "md5", 40: "sha1", 64: "sha256",
    128: "sha512",                   # ← new
}
```

Everything else (index build, binary search, caching, filenames) adapts automatically.

**Add third-party packages** — list them in `requirements.txt` and `install.py` will install them on the next run.

---

## ⚠️ Legal & Ethical Notice

> **H CRACKER is a security research and education tool.**
>
> Only run it against hashes **you own** or have **explicit written permission** to test. Using it to access accounts, systems, or data you do not own is illegal in most jurisdictions and is not what this project is for.
>
> The author is **not responsible** for misuse. By using this tool you agree to use it responsibly and in accordance with all applicable laws.

---

## 🙌 Credits

- Wordlist data: [SecLists](https://github.com/danielmiessler/SecLists) & [RockYou](https://github.com/josuamarcelc/common-password-list)
- Design idea: *"What if John the Ripper, but it respected your RAM?"*

---

## 📄 License

Released under the **MIT License**. See [`LICENSE`](LICENSE) for details.

---

<div align="center">

**Made with 🐍, ⚡, and way too many hex characters.**

If H CRACKER helped you, drop a ⭐ on the repo.

</div>
