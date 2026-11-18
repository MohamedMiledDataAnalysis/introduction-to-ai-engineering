"""Every script printed in solutions/*.md under a file path must be the same code as that file.
Run from the root of the repository:  python tests/test_solutions_files.py"""
import re
from pathlib import Path

LISTING = re.compile(r"^`((?:chapters|aie|aie_r|apps|services|tests)/[^`]+\.(?:py|R))`\n\n``` \w+\n(.*?)\n```$", re.M | re.S)
problems = checked = 0
for md in sorted(Path("solutions").glob("ch*_corrections.md")):
    for path, code in LISTING.findall(md.read_text(encoding="utf-8")):
        checked += 1
        lines = Path(path).read_text(encoding="utf-8").splitlines(keepends=True)
        i = 0
        while i < len(lines) and lines[i].startswith("#"): i += 1   # title comment of the file
        while i < len(lines) and lines[i].strip() == "": i += 1
        if "".join(lines[i:]) != code + "\n":
            print("DIFFERS", md.name, path); problems += 1
print(f"{checked} scripts checked against solutions/: ", "all identical" if problems == 0 else f"{problems} differ")
assert problems == 0
