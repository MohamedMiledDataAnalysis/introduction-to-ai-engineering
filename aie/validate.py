"""Turn a model's reply into a Python object and check it against a small JSON schema."""
import json
import re


def parse_json_reply(text):
    """Extract the first JSON object from a reply, tolerating code fences and surrounding text."""
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    start = cleaned.find("{")
    if start == -1:
        raise ValueError("no JSON object in the reply")
    depth = 0
    for i, ch in enumerate(cleaned[start:], start):
        depth += ch == "{"
        depth -= ch == "}"
        if depth == 0:
            return json.loads(cleaned[start:i + 1])
    raise ValueError("unbalanced braces in the reply")


TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "object": dict, "array": list}


def validate(obj, schema):
    """Return a list of error messages; an empty list means the object is valid."""
    errors = []
    for field in schema.get("required", []):
        if field not in obj:
            errors.append(f"missing field '{field}'")
    for field, rule in schema.get("properties", {}).items():
        if field not in obj:
            continue
        value = obj[field]
        allowed = rule["type"] if isinstance(rule["type"], list) else [rule["type"]]
        if value is None:
            if "null" not in allowed:
                errors.append(f"'{field}' must not be null")
            continue
        py = tuple(t for a in allowed if a != "null" for t in
                   (TYPES[a] if isinstance(TYPES[a], tuple) else (TYPES[a],)))
        if isinstance(value, bool) and bool not in py:
            errors.append(f"'{field}' has type boolean, expected {allowed}")
            continue
        if not isinstance(value, py):
            errors.append(f"'{field}' has type {type(value).__name__}, expected {allowed}")
            continue
        if "enum" in rule and value not in rule["enum"]:
            errors.append(f"'{field}' = {value!r} is not one of {rule['enum']}")
        if "minimum" in rule and value < rule["minimum"]:
            errors.append(f"'{field}' = {value} is below the minimum {rule['minimum']}")
        if "pattern" in rule and not re.fullmatch(rule["pattern"], value):
            errors.append(f"'{field}' = {value!r} does not match {rule['pattern']}")
    extra = set(obj) - set(schema.get("properties", {}))
    if extra and schema.get("additionalProperties") is False:
        errors.append(f"unexpected fields {sorted(extra)}")
    return errors
