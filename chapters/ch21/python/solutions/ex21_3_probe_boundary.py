# Exercise 21.3 - Probe the boundary of the SF scope guard, and show the test protecting it
# Run from the root of the repository:  python chapters/ch21/python/solutions/ex21_3_probe_boundary.py
import re
import sys

sys.path.insert(0, ".")
import aie.assistants as A

sf = A.Assistant("sf")
probes = ["Compare the HGEF factsheet with the HECB KID.",
          "Which fund does the Larkfield reserve fund protect?",
          "What is the bond fund duration?",
          "Which notes does the reserve fund protect?",
          "What is the duration of the euro credit product?"]


def show(title):
    print(title)
    for q in probes:
        r = sf.guard_question(q)
        print(f"  {'refused ' if r == A.OUT_OF_SCOPE_SF else 'accepted'}  {q}")


show("Guard as shipped:")

# Change 1: add 'fund' on its own to the asset management words
shipped_words, shipped_guard = A.AM_WORDS, A.Assistant.guard_question
A.AM_WORDS = re.compile(shipped_words.pattern.replace("equity fund|bond fund", "equity fund|bond fund|fund"), re.I)
show("Change 1, 'fund' added to AM_WORDS:")


# Change 2: on top of change 1, simplify the rule to 'refuse any question with an AM word'
def simplified(self, question):
    if self.domain == "sf" and A.AM_WORDS.search(question):
        return A.OUT_OF_SCOPE_SF
    return shipped_guard(self, question)


A.Assistant.guard_question = simplified
show("Change 2, and the rule simplified:")
ok = sf.guard_question("Which fund does the Larkfield reserve fund protect?") is None
print("Test 'SF accepts fund in a Larkfield question':", "PASS" if ok else "FAIL")
A.AM_WORDS, A.Assistant.guard_question = shipped_words, shipped_guard
