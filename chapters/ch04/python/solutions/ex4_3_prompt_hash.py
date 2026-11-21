# Exercise 4.3 - Hash of prompt version 2
# Run from the root of the repository:  python chapters/ch04/python/solutions/ex4_3_prompt_hash.py

import shutil
import sys
from pathlib import Path

sys.path.insert(0, ".")
# Step 1, done from the reference copy if you have not written the file yet
if not Path("prompts/extract_servicer_note_v2.txt").exists():
    shutil.copy("prompts/solutions/extract_servicer_note_v2.txt", "prompts/")

from aie.prompts import load_prompt
print(load_prompt("extract_servicer_note_v2")[1])
