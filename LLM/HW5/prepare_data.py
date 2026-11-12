"""Prepare only Team-ACE/ToolACE; split whole dialogues BEFORE unrolling."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re

from rewards import canonical, source_calls, render_calls, score

MODEL = "Qwen/Qwen3.5-2B"
REVISION = "15852e8c16360a2fea060d615a32b45270f8a8fc"
DATASET_REVISION = "6bda777c88d21e5a204703c1ee45597a8fa4f734"
SEED = 42
MAX_PROMPT = 1536


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def schema(value):
    if isinstance(value, list):
        return [schema(v) for v in value]
    if not isinstance(value, dict):
        return value
    result = {k: schema(v) for k, v in value.items() if v is not None}
    if isinstance(result.get("type"), str):
        result["type"] = {
            "dict": "object",
            "float": "number",
            "tuple": "array",
            "any": "string",
        }.get(result["type"], result["type"])
    return result


def extract_tools(system):
    marker = "Here is a list of functions in JSON format that you can invoke:"
    start = system.index("[", system.index(marker) + len(marker))
    functions, _ = json.JSONDecoder().raw_decode(system[start:])
    assert isinstance(functions, list) and functions
    aliases, used, tools = {}, set(), []
    for function in functions:
        original = function["name"]
        name = re.sub(r"\W", "_", original).strip("_") or "tool"
        if name[0].isdigit():
            name = "tool_" + name
        candidate, n = name, 1
        while candidate in used:
            n += 1
            candidate = f"{name}_{n}"
        aliases[original] = candidate
        used.add(candidate)
        tools.append(
            dict(
                type="function",
                function=dict(
                    name=candidate,
                    description=function.get("description", ""),
                    parameters=schema(
                        function.get("parameters", {"type": "object", "properties": {}})
                    ),
                ),
            )
        )
    return tools, aliases


def balanced(rows, limit, rng):
    yes = [r for r in rows if r["kind"] == "call"]
    no = [r for r in rows if r["kind"] == "no_call"]
    rng.shuffle(yes)
    rng.shuffle(no)
    selected = yes[: int(limit * 0.75)] + no[: limit - int(limit * 0.75)]
    rng.shuffle(selected)
    return selected


def main():
    from datasets import load_dataset
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
    data = load_dataset("Team-ACE/ToolACE", revision=DATASET_REVISION, split="train")
    splits = dict(train=[], validation=[])
    counts, seen, lengths, targets, tool_counts = Counter(), set(), [], [], []
    for index, row in enumerate(data):
        digest = sha(canonical(row))
        if digest in seen:
            counts["duplicate_dialogue"] += 1
            continue
        seen.add(digest)
        split = (
            "validation" if int(sha(str(SEED) + digest)[:8], 16) % 20 == 0 else "train"
        )
        try:
            tools, aliases = extract_tools(row["system"])
        except (ValueError, KeyError, AssertionError):
            counts["bad_tools"] += 1
            continue
        history = []
        tool_counts.append(len(tools))
        for message in row["conversations"]:
            role, value = message["from"], message["value"]
            if role == "user":
                history.append(dict(role="user", content=value))
            elif role == "tool":
                history.append(dict(role="tool", content=value))
            elif role == "assistant":
                try:
                    calls = source_calls(value, aliases)
                except (ValueError, SyntaxError, TypeError, KeyError):
                    counts["unparseable_source_call"] += 1
                    break  # do not make future prefixes with a corrupted call history
                if history and history[-1]["role"] == "user":
                    counts["user_assistant_turns"] += 1
                    prompt = tokenizer.apply_chat_template(
                        history,
                        tools=tools,
                        tokenize=False,
                        add_generation_prompt=True,
                        enable_thinking=False,
                    )
                    length = len(tokenizer.encode(prompt, add_special_tokens=False))
                    target = render_calls(calls) if calls else value
                    target_length = len(
                        tokenizer.encode(target, add_special_tokens=False)
                    )
                    lengths.append(length)
                    targets.append(target_length)
                    kind = "call" if calls else "no_call"
                    counts[kind] += 1
                    if (
                        length <= MAX_PROMPT
                        and target_length <= 384
                        and score(target, calls, tools, "exact") == 1
                    ):
                        splits[split].append(
                            dict(
                                prompt=prompt,
                                reference_calls=json.dumps(calls, ensure_ascii=False),
                                tools_json=json.dumps(tools, ensure_ascii=False),
                                dialog_id=digest,
                                turn=len(history),
                                kind=kind,
                            )
                        )
                    else:
                        counts["filtered_length_or_schema"] += 1
                if calls:
                    history.append(
                        dict(
                            role="assistant",
                            content="",
                            tool_calls=[
                                dict(type="function", function=c) for c in calls
                            ],
                        )
                    )
                else:
                    history.append(dict(role="assistant", content=value))
        if (index + 1) % 1000 == 0:
            print("prepared dialogues", index + 1, flush=True)
    train = balanced(splits["train"], 1536, random.Random(SEED))
    validation = balanced(splits["validation"], 128, random.Random(SEED))
    assert len(train) >= 512 and len(validation) >= 32
    assert not {r["dialog_id"] for r in train} & {r["dialog_id"] for r in validation}
    root = Path(__file__).resolve().parent
    (root / "data").mkdir(exist_ok=True)
    hashes = {}
    for name, rows in (("train", train), ("validation", validation)):
        path = root / "data" / (name + ".jsonl")
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()

    def stats(values):
        values = sorted(values)
        return dict(
            min=values[0],
            median=values[len(values) // 2],
            p90=values[int(len(values) * 0.9)],
            p99=values[int(len(values) * 0.99)],
            max=values[-1],
        )

    eda = dict(
        dataset="Team-ACE/ToolACE",
        dataset_revision=DATASET_REVISION,
        model=MODEL,
        model_revision=REVISION,
        seed=SEED,
        source_dialogues=len(data),
        unique_dialogues=len(seen),
        counts=dict(counts),
        prompt_tokens=stats(lengths),
        reference_tokens=stats(targets),
        tools_per_dialogue=stats(tool_counts),
        candidates={k: len(v) for k, v in splits.items()},
        selected={
            k: dict(
                total=len(v),
                kinds=dict(Counter(r["kind"] for r in v)),
                dialogues=len({r["dialog_id"] for r in v}),
            )
            for k, v in (("train", train), ("validation", validation))
        },
        dialogue_overlap=0,
        sha256=hashes,
        tokenizer_template_sha256=sha(tokenizer.chat_template),
    )
    (root / "data/eda.json").write_text(
        json.dumps(eda, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(eda, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
