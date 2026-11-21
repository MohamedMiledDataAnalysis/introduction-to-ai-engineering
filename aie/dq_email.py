"""Draft the data query to the servicer with a model, then check it against the list of issues."""
import re

from aie.llm import chat
from aie.prompts import load_prompt, render

LOAN_ID = re.compile(r"LMF25-\d{5}")


def issues_text(found):
    return "\n".join(f"- {r.loan_id}: {r.description}" for r in found.itertuples())


def draft_email(found, cutoff_date, deadline):
    template, version = load_prompt("servicer_query_email_v1")
    prompt = render(template, cutoff_date=cutoff_date, deadline=deadline, issues=issues_text(found))
    return chat([{"role": "user", "content": prompt}], temperature=0.2)["text"].strip(), version


def check_email(email, found):
    expected, written = set(found["loan_id"]), LOAN_ID.findall(email)
    problems = [f"loan {x} is not in the issue list"
                for x in sorted(set(written) - expected)]
    problems += [f"loan {x} is missing from the email"
                 for x in sorted(expected - set(written))]
    problems += [f"loan {x} is mentioned {written.count(x)} times"
                 for x in sorted(set(written)) if written.count(x) > 1]
    return problems


def template_email(found, cutoff_date, deadline):
    """Fallback without a model: always complete, never wrong, less readable."""
    return (f"Dear colleagues,\n\nOur checks of the loan-level tape for {cutoff_date} found the following issues. "
            f"Please confirm or correct each one and send a corrected tape by {deadline}.\n\n{issues_text(found)}\n\n"
            "Kind regards,\nLarkfield 2025-1 Cash Management")
