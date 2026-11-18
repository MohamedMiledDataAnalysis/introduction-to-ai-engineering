# Chapter 4 - Turn replies into data, and reject the bad ones
import json
import sys

sys.path.insert(0, ".")
from aie.validate import parse_json_reply, validate

schema = json.load(open("prompts/servicer_note_schema.json"))

replies = {
    "A clean JSON": '{"loan_id": "LMF25-00190", "months_in_arrears": 3, '
        '"arrears_balance": 1960.79, "action": "payment_plan", '
        '"promise_date": "2026-10-28"}',
    "B fenced, with a preface": 'Here is the JSON:\n```json\n'
        '{"loan_id": "LMF25-00168", "months_in_arrears": 2, '
        '"arrears_balance": 829.85, "action": "no_contact", '
        '"promise_date": null}\n```',
    "C number as text": '{"loan_id": "LMF25-00321", '
        '"months_in_arrears": "one", "arrears_balance": 938.63, '
        '"action": "no_contact", "promise_date": null}',
    "D label outside the list": '{"loan_id": "LMF25-00190", '
        '"months_in_arrears": 3, "arrears_balance": 1960.79, '
        '"action": "payment plan", "promise_date": "28/10/2026"}',
    "E missing field": '{"loan_id": "LMF25-00190", '
        '"arrears_balance": 1960.79, "action": "payment_plan", '
        '"promise_date": "2026-10-28"}',
}
for name, reply in replies.items():
    try:
        obj = parse_json_reply(reply)
    except ValueError as err:
        print(f"{name:<26} NOT JSON: {err}")
        continue
    errors = validate(obj, schema)
    print(f"{name:<26} {'valid' if not errors else 'INVALID'}")
    for e in errors:
        print(f"{'':<28}- {e}")
