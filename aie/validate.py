"""Turn a model's reply into a Python object and check it against a small JSON schema."""
import json
import re


def parse_json_reply(text):
    """Extract the first JSON object from a reply, tolerating code fences and surrounding text.

    raw_decode() reads one complete JSON value and stops, so braces inside strings
    ("note": "see {Section 4}") and text after the object do not disturb it.
    """
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    decoder = json.JSONDecoder()
    start = cleaned.find("{")
    if start == -1:
        raise ValueError("no JSON object in the reply")
    while start != -1:
        try:
            obj, _ = decoder.raw_decode(cleaned, start)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
        start = cleaned.find("{", start + 1)
    raise ValueError("no valid JSON object in the reply")


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
        if isinstance(value, float) and value.is_integer() and "integer" in allowed:
            value = int(value)                          # JSON has one number type: 12.0 is an integer
        if not isinstance(value, py):
            errors.append(f"'{field}' has type {type(value).__name__}, expected {allowed}")
            continue
        if "enum" in rule and value not in rule["enum"]:
            errors.append(f"'{field}' = {value!r} is not one of {[e for e in rule['enum'] if e is not None]}")
        if "minimum" in rule and value < rule["minimum"]:
            errors.append(f"'{field}' = {value} is below the minimum {rule['minimum']}")
        if "pattern" in rule and not re.fullmatch(rule["pattern"], value):
            errors.append(f"'{field}' = {value!r} does not match {rule['pattern']}")
    extra = set(obj) - set(schema.get("properties", {}))
    if extra and schema.get("additionalProperties") is False:
        errors.append(f"unexpected fields {sorted(extra)}")
    return errors
