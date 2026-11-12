"""Pure, non-executing parsers and rewards. BFCL is never used for training."""

import ast
from collections import Counter
import json
import re

CALL = re.compile(
    r"<tool_call>\s*<function=([^>]+)>\s*(.*?)\s*</function>\s*</tool_call>", re.S
)
PARAM = re.compile(r"<parameter=([^>]+)>\s*(.*?)\s*</parameter>", re.S)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def source_calls(text, aliases):
    """Read ToolACE Python-like calls, including names containing spaces; never eval."""
    if not text.strip().startswith("["):
        return []
    names = sorted(aliases, key=len, reverse=True)
    parts, i, quote, escaped = [], 0, None, False
    while i < len(text):
        char = text[i]
        if quote:
            parts.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            i += 1
            continue
        if char in "\"'":
            quote = char
        elif i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_"):
            match = next(
                (
                    name
                    for name in names
                    if text.startswith(name, i)
                    and text[i + len(name) :].lstrip().startswith("(")
                ),
                None,
            )
            if match:
                parts.append(aliases[match])
                i += len(match)
                continue
        parts.append(char)
        i += 1
    tree = ast.parse("".join(parts), mode="eval").body
    if not isinstance(tree, ast.List):
        raise ValueError("Expected a call list")

    def literal(node):
        if isinstance(node, ast.Name) and node.id in ("true", "false", "null"):
            return {"true": True, "false": False, "null": None}[node.id]
        if isinstance(node, (ast.List, ast.Tuple)):
            return [literal(v) for v in node.elts]
        if isinstance(node, ast.Dict):
            return {literal(k): literal(v) for k, v in zip(node.keys, node.values)}
        return ast.literal_eval(node)

    calls = []
    for node in tree.elts:
        if (
            not isinstance(node, ast.Call)
            or not isinstance(node.func, ast.Name)
            or node.args
        ):
            raise ValueError("Expected named function calls with keyword arguments")
        if node.func.id not in aliases.values() or any(
            k.arg is None for k in node.keywords
        ):
            raise ValueError("Unknown call or argument expansion")
        calls.append(
            dict(
                name=node.func.id,
                arguments={k.arg: literal(k.value) for k in node.keywords},
            )
        )
    return calls


def parse_completion(text, tools):
    text = text.replace("<|im_end|>", "").replace("<|endoftext|>", "").strip()
    if not text:
        return None
    functions = {t["function"]["name"]: t["function"] for t in tools}
    calls = []
    for match in CALL.finditer(text):
        name, body = match.group(1).strip(), match.group(2)
        if name not in functions:
            return None
        schema = functions[name]["parameters"]
        arguments = {}
        for parameter in PARAM.finditer(body):
            key, raw = parameter.group(1).strip(), parameter.group(2).strip()
            if key in arguments or key not in schema.get("properties", {}):
                return None
            kind = schema["properties"][key].get("type", "string")
            try:
                value = raw if kind == "string" else json.loads(raw)
            except (ValueError, TypeError):
                return None
            if kind == "integer" and type(value) is not int:
                return None
            if kind == "number" and (
                not isinstance(value, (int, float)) or isinstance(value, bool)
            ):
                return None
            if kind == "boolean" and type(value) is not bool:
                return None
            if kind == "array" and not isinstance(value, list):
                return None
            if kind == "object" and not isinstance(value, dict):
                return None
            arguments[key] = value
        if PARAM.sub("", body).strip():
            return None
        # Missing required arguments are scored as an argument error, not format failure.
        calls.append(dict(name=name, arguments=arguments))
    remainder = CALL.sub("", text)
    if any(
        marker in remainder
        for marker in (
            "<tool",
            "</tool",
            "<function",
            "</function",
            "<parameter",
            "</parameter",
        )
    ):
        return None
    return calls


def f1(left, right):
    a, b = Counter(left), Counter(right)
    if not a and not b:
        return 1.0
    return 2 * sum((a & b).values()) / (sum(a.values()) + sum(b.values()))


def reward_parts(text, expected, tools):
    calls = parse_completion(text, tools)
    if calls is None:
        return dict(format=0.0, names=0.0, arguments=0.0, exact=0.0)
    exact = float(Counter(map(canonical, calls)) == Counter(map(canonical, expected)))
    if not expected:
        value = float(not calls)
        return dict(format=value, names=value, arguments=value, exact=value)
    names = f1([c["name"] for c in calls], [c["name"] for c in expected])

    def atoms(items):
        return [
            (c["name"], key, canonical(value))
            for c in items
            for key, value in c["arguments"].items()
        ]

    actual_args, expected_args = atoms(calls), atoms(expected)
    arguments = (
        f1(actual_args, expected_args) if actual_args or expected_args else names
    )
    return dict(format=1.0, names=names, arguments=arguments, exact=exact)


def score(text, expected, tools, mode="dense"):
    values = reward_parts(text, expected, tools)
    if mode == "exact":
        return values["exact"]
    return (
        0.1 * values["format"]
        + 0.2 * values["names"]
        + 0.3 * values["arguments"]
        + 0.4 * values["exact"]
    )


def make_reward(mode):
    def tool_reward(completions, reference_calls, tools_json, **kwargs):
        texts = [
            c if isinstance(c, str) else "".join(m.get("content", "") or "" for m in c)
            for c in completions
        ]
        return [
            score(text, json.loads(expected), json.loads(tools), mode)
            for text, expected, tools in zip(
                texts, reference_calls, tools_json, strict=True
            )
        ]

    tool_reward.__name__ = mode + "_tool_reward"
    return tool_reward


def render_calls(calls):
    blocks = []
    for call in calls:
        parameters = []
        for key, value in call["arguments"].items():
            text = (
                value
                if isinstance(value, str)
                else json.dumps(value, ensure_ascii=False)
            )
            parameters.append(f"<parameter={key}>\n{text}\n</parameter>")
        blocks.append(
            "<tool_call>\n<function="
            + call["name"]
            + ">\n"
            + "\n".join(parameters)
            + "\n</function>\n</tool_call>"
        )
    return "\n".join(blocks)
