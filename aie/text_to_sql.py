"""Ask the Harbourline database a question in English: the model writes SQL, code guards and runs it."""
import json

from aie.factcheck import check_signed
from aie.llm import chat
from aie.prompts import load_prompt, render
from aie.sqlguard import run_sql
from aie.validate import parse_json_reply

SQL_SCHEMA = {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]}


def ask_database(question, retries=1):
    template, version = load_prompt("text_to_sql_v1")
    schema_text, _ = load_prompt("am_schema")
    messages = [{"role": "user", "content": render(template, schema=schema_text, question=question)}]
    for attempt in range(retries + 1):
        reply = chat(messages, format=SQL_SCHEMA)
        try:
            sql = parse_json_reply(reply["text"])["sql"]
        except (ValueError, KeyError):
            return {"question": question, "error": "no SQL in the reply", "prompt": version}
        result = run_sql(sql)
        if "error" not in result:
            break
        messages += [{"role": "assistant", "content": reply["text"]},
                     {"role": "user", "content": f"That query failed: {result['error']}. Write a corrected query."}]
    return {"question": question, "sql": sql, "result": result, "prompt": version}


def explain_result(question, out):
    """Second call: the model states the answer in one sentence from the rows; figures are then checked."""
    rows = json.dumps({"columns": out["result"]["columns"], "rows": out["result"]["rows"][:20]})
    text = chat([{"role": "user", "content":
                  f"QUESTION: {question}\nQUERY RESULT: {rows}\nAnswer in one sentence using only the result. "
                  "Express decimals that are weights or returns as percentages with two decimals."}])["text"]
    facts = {}
    for i, row in enumerate(out["result"]["rows"]):
        for j, v in enumerate(row):
            if isinstance(v, (int, float)):
                facts[f"r{i}c{j}"] = (v * 100, "percent")      # a decimal shown as a percentage
                facts[f"r{i}c{j}n"] = (v, "number")
                facts[f"r{i}c{j}m"] = (v, "money")
    unsupported = [f.raw for f, hits in check_signed(text, facts) if not hits]
    return text.strip(), unsupported
