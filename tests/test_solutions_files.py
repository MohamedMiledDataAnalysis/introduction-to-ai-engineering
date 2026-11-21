"""Every block of code printed in solutions/*.md under a file path must be in that file:
the whole file when the label is the path alone, the same lines in the same order when it says (extract).
Run from the root of the repository:  python tests/test_solutions_files.py"""
import re
from pathlib import Path

LISTING = re.compile(r"^`((?:chapters|aie|aie_r|apps|services|tests|agents|governance|prompts)/[^`]+)`"
                     r"( \(extract\))?\n\n``` ?\w+\n(.*?)\n```$", re.M | re.S)


def body_of(path):
    """The file without its leading comment lines and the blank lines after them."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines) and lines[i].startswith("#") and not lines[i].startswith("#*"):
        i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    return "\n".join(lines[i:]).rstrip("\n")


def code_only(line):
    """Without indentation, trailing comment, or the brackets and commas that close the line."""
    return re.sub(r"\s{2,}#.*$", "", line).strip().rstrip(" ,;)")


def missing_line(block, path):
    real = [code_only(l) for l in Path(path).read_text(encoding="utf-8").splitlines()]
    i = 0
    for line in block.splitlines():
        s = code_only(line)
        if not s or "..." in s or "…" in s:
            continue
        while i < len(real) and real[i] != s:
            i += 1
        if i == len(real):
            return s
        i += 1
    return None


problems = whole = extracts = 0
for md in sorted(Path("solutions").glob("ch*_corrections.md")):
    for path, extract, code in LISTING.findall(md.read_text(encoding="utf-8")):
        if extract:
            extracts += 1
            miss = missing_line(code, path)
            if miss:
                print("NOT IN FILE", md.name, path, repr(miss[:70])); problems += 1
        else:
            whole += 1
            full = Path(path).read_text(encoding="utf-8").rstrip("\n")
            if code.rstrip("\n") not in (full, body_of(path)):    # with or without the title comment
                print("DIFFERS", md.name, path); problems += 1
print(f"{whole} whole scripts and {extracts} extracts checked against solutions/: ",
      "all identical" if problems == 0 else f"{problems} differ")
assert problems == 0
