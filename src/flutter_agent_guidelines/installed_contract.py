"""Portable, self-attested lint contracts; never inspect or execute a consumer."""

import json
import math
import re

from .bundles import read_resource
from .snapshots import SnapshotError, checked_path, regular_bytes, require_digest

MAX_BYTES = 1024 * 1024


def bounded(value, depth=0, budget=None):
    """Accept bounded interoperable JSON, rejecting nonfinite numbers/surrogates."""
    budget = [20000] if budget is None else budget
    budget[0] -= 1
    if depth > 16 or budget[0] < 0:
        raise SnapshotError("lint contract exceeds JSON depth/node limits")
    if isinstance(value, str):
        if len(value) > 16384:
            raise SnapshotError("lint contract string too long")
        try:
            value.encode("utf-8")
        except UnicodeError as error:
            raise SnapshotError("invalid lint contract Unicode") from error
    elif value is None or type(value) is bool:
        return
    elif type(value) is int:
        if abs(value) > 2 ** 53 - 1:
            raise SnapshotError("lint contract integer exceeds interoperable range")
    elif type(value) is float:
        if not math.isfinite(value):
            raise SnapshotError("nonfinite lint contract number")
    elif isinstance(value, list):
        if len(value) > 4096:
            raise SnapshotError("lint contract array too long")
        for item in value:
            bounded(item, depth + 1, budget)
    elif isinstance(value, dict):
        if len(value) > 256:
            raise SnapshotError("lint contract object too large")
        for key, item in value.items():
            if not isinstance(key, str) or len(key) > 256:
                raise SnapshotError("invalid lint contract object key")
            bounded(key, depth + 1, budget)
            bounded(item, depth + 1, budget)
    else:
        raise SnapshotError("invalid lint contract JSON type")


def canonical_contract(value):
    """Exporter encoding: UTF-16 key order, compact UTF-8, array order, one LF."""
    bounded(value)

    def encode(item):
        if isinstance(item, dict):
            keys = sorted(item, key=lambda key: key.encode("utf-16-be"))
            return "{" + ",".join(encode(key) + ":" + encode(item[key]) for key in keys) + "}"
        if isinstance(item, list):
            return "[" + ",".join(encode(child) for child in item) + "]"
        if type(item) is float:
            # Dart double.toString uses fixed notation for [1e-6, 1e21),
            # and exponents without zero padding outside that interval.
            text = repr(item)
            if "e" in text:
                mantissa, exponent = text.split("e")
                power = int(exponent)
                if -6 <= power < 21:
                    from decimal import Decimal
                    text = format(Decimal(text), "f")
                    if "." not in text:
                        text += ".0"
                else:
                    text = mantissa.removesuffix(".0") + "e" + ("+" if power >= 0 else "-") + str(abs(power))
            return text
        return json.dumps(item, ensure_ascii=False, allow_nan=False, separators=(",", ":"))

    raw = (encode(value) + "\n").encode("utf-8")
    if len(raw) > MAX_BYTES:
        raise SnapshotError("lint contract exceeds byte limit")
    return raw


def selection():
    text = read_resource("profiles/architecture.md").decode("utf-8")
    rows = re.findall(r"^\|\s*`([a-z][a-z0-9_]*)`\s*\|\s*(enabled|disabled)\s*\|", text, re.M)
    expected = {name: state == "enabled" for name, state in rows}
    required = ("method_order", "variable_name_should_contain_class_name", "require_explicit_types")
    if (len(rows) != 51 or len(expected) != 51 or
            any(expected.get(name) is not True for name in required)):
        raise SnapshotError("installed architecture diagnostic table must contain 51 unique rules")
    return expected


def validate(value, profiles, align=True):
    bounded(value)
    if (not isinstance(value, dict) or set(value) != {
            "schema", "package", "version", "profile", "source_digest", "rules"}
            or type(value["schema"]) is not int or value["schema"] != 1
            or value["package"] != "dart_architecture_lints"
            or not isinstance(value["version"], str)
            or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?", value["version"])
            or value["profile"] != "architecture" or "architecture" not in profiles
            or not isinstance(value["rules"], dict) or not value["rules"]):
        raise SnapshotError("invalid lint contract schema/package/version/profile; architecture selection required")
    require_digest(value["source_digest"])
    for name, rule in value["rules"].items():
        if (not re.fullmatch(r"[a-z][a-z0-9_]*", name) or not isinstance(rule, dict)
                or set(rule) != {"enabled", "options", "severity"}
                or type(rule["enabled"]) is not bool or not isinstance(rule["options"], dict)
                or rule["severity"] not in ("INFO", "WARNING", "ERROR")):
            raise SnapshotError(f"invalid lint contract rule: {name}")
    if align:
        expected = selection()
        if set(value["rules"]) != set(expected):
            raise SnapshotError("lint contract rule IDs differ from installed architecture table")
        if any(value["rules"][name]["enabled"] != enabled for name, enabled in expected.items()):
            raise SnapshotError("lint contract enabled states differ from installed architecture table")
        if value["rules"]["require_explicit_types"]["options"].get("policy") != "selective":
            raise SnapshotError("architecture lint contract requires selective typing policy")
    return value


def load(path, max_bytes=MAX_BYTES):
    path = checked_path(path)
    if path.stat().st_size > max_bytes:
        raise SnapshotError("lint contract exceeds byte limit")
    raw = regular_bytes(path)
    if len(raw) > max_bytes:
        raise SnapshotError("lint contract exceeds byte limit")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise SnapshotError("duplicate lint contract JSON key")
            result[key] = value
        return result

    def invalid_constant(_value):
        raise SnapshotError("nonfinite lint contract number")

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                           parse_constant=invalid_constant)
        bounded(value)
        return value
    except (ValueError, UnicodeError, RecursionError) as error:
        raise SnapshotError(f"invalid lint contract JSON: {error}") from error


def attachment(previous, supplied=None, clear=False):
    if clear and supplied is not None:
        raise SnapshotError("cannot supply and clear a lint contract together")
    return None if clear else supplied if supplied is not None else (previous or {}).get("lint_contract")


def summary(pin):
    contract = pin.get("lint_contract")
    if contract is None:
        return {"state": "unrecorded", "runtime_verification": "not performed"}
    return {"state": "recorded, not installed-runtime verified",
            "digest": pin["lint_contract_digest"], "package": contract["package"],
            "version": contract["version"], "source_digest": contract["source_digest"],
            "profile": contract["profile"]}


def description(pin):
    info = summary(pin)
    if info["state"] == "unrecorded":
        return "Lint contract: unrecorded (guidance-only; lint runtime unverified).\n"
    return (f"Lint contract: RECORDED, NOT installed-runtime verified; {info['package']} "
            f"{info['version']}; contract SHA-256 {info['digest']}; "
            f"source SHA-256 {info['source_digest']}.\n")
