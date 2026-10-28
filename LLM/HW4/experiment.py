"""Qwen2.5-1.5B: full FT and one-factor-at-a-time LoRA experiments."""
import argparse
import collections
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import sys
import time

# Optional private PEFT install on the teaching server; no shared env changes.
sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
DATASET = "dair-ai/emotion"
SEED = 42
N_TRAIN = 10_000
TEXT_TOKENS = 128
MAX_LENGTH = 256
LABELS = ["sadness", "joy", "love", "anger", "fear", "surprise"]
TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
LORA = dict(r=8, lora_alpha=16, lora_dropout=0.0, target_modules=["q_proj", "v_proj"])
RUNS = {
    "base": None,
    "full": None,
    "lora": LORA,
    "lora_r16": {**LORA, "r": 16},
    "lora_alpha32": {**LORA, "lora_alpha": 32},
    "lora_dropout01": {**LORA, "lora_dropout": 0.1},
    "lora_all": {**LORA, "target_modules": TARGETS},
}
SYSTEM = (
    "Classify the emotion in the text. Reply with exactly one digit and nothing else. "
    "0=sadness, 1=joy, 2=love, 3=anger, 4=fear, 5=surprise."
)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(root):
    from datasets import load_dataset
    from huggingface_hub import HfApi, snapshot_download

    manifest = root / "outputs/data_manifest.json"
    reference = manifest if manifest.exists() else Path(__file__).resolve().parent / "outputs/data_manifest.json"
    previous = json.loads(reference.read_text()) if reference.exists() else None
    patterns = ["*.safetensors", "config.json", "generation_config.json", "tokenizer*", "vocab.json", "merges.txt"]
    if manifest.exists() and (root / "data/train.jsonl").exists() and (root / "data/test.jsonl").exists():
        info = previous
        assert sha(root / "data/train.jsonl") == info["train_sha256"]
        assert sha(root / "data/test.jsonl") == info["test_sha256"]
        print("Prepared data already exist and hashes match.", flush=True)
        snapshot_download(MODEL, revision=info["model_revision"], allow_patterns=patterns, max_workers=4)
        return
    api = HfApi()
    dataset_revision = previous["dataset_revision"] if previous else api.dataset_info(DATASET).sha
    model_revision = previous["model_revision"] if previous else api.model_info(MODEL).sha
    data = load_dataset(DATASET, "split", revision=dataset_revision)
    assert data["train"].features["label"].names == LABELS
    test = [dict(id=i, text=row["text"], label=row["label"]) for i, row in enumerate(data["test"])]
    assert len(test) == 2000
    normalize = lambda text: " ".join(text.lower().split())
    test_texts = {normalize(row["text"]) for row in test}
    train = []
    shuffled = data["train"].add_column("source_id", list(range(len(data["train"]))))
    shuffled = shuffled.shuffle(seed=SEED)
    selected_texts = set()
    for row in shuffled:
        text = normalize(row["text"])
        if text in test_texts or text in selected_texts:
            continue
        selected_texts.add(text)
        train.append(dict(id=row["source_id"], text=row["text"], label=row["label"]))
        if len(train) == N_TRAIN:
            break
    assert len(train) == N_TRAIN and not selected_texts & test_texts
    write_rows(root / "data/train.jsonl", train)
    write_rows(root / "data/test.jsonl", test)
    if previous:
        assert sha(root / "data/train.jsonl") == previous["train_sha256"]
        assert sha(root / "data/test.jsonl") == previous["test_sha256"]
    manual_ids = [next(r["id"] for r in test if r["label"] == label) for label in range(6)]
    manual_ids += [r["id"] for r in test if r["id"] not in manual_ids][:2]
    examples = [next(r for r in train if r["label"] == label) for label in (0, 1, 4)]
    info = dict(
        dataset=DATASET, dataset_config="split", dataset_revision=dataset_revision,
        model=MODEL, model_revision=model_revision, seed=SEED,
        original_sizes={key: len(value) for key, value in data.items()},
        train_size=len(train), test_size=len(test),
        train_sha256=sha(root / "data/train.jsonl"), test_sha256=sha(root / "data/test.jsonl"),
        train_counts=dict(collections.Counter(LABELS[r["label"]] for r in train)),
        test_counts=dict(collections.Counter(LABELS[r["label"]] for r in test)),
        train_test_text_overlap=0, train_unique_texts=len(selected_texts),
        manual_ids=manual_ids, dataset_examples=examples,
    )
    write_json(manifest, info)
    print(json.dumps(info, ensure_ascii=False, indent=2), flush=True)
    # Only safe weights/tokenizer files; no remote Python code.
    snapshot_download(
        MODEL, revision=model_revision,
        allow_patterns=patterns,
        max_workers=4,
    )


def metrics(gold, predicted):
    assert len(gold) == len(predicted) and len(gold) > 0
    per_class = {}
    for label, name in enumerate(LABELS):
        tp = sum(a == label and b == label for a, b in zip(gold, predicted))
        fp = sum(a != label and b == label for a, b in zip(gold, predicted))
        fn = sum(a == label and b != label for a, b in zip(gold, predicted))
        per_class[name] = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
    return dict(
        accuracy=sum(a == b for a, b in zip(gold, predicted)) / len(gold),
        macro_f1=sum(per_class.values()) / len(LABELS),
        invalid_rate=sum(b == -1 for b in predicted) / len(predicted),
        per_class_f1=per_class,
    )


def prompts(tokenizer, rows):
    result = []
    for row in rows:
        tokens = tokenizer.encode(row["text"], add_special_tokens=False)[:TEXT_TOKENS]
        text = tokenizer.decode(tokens, skip_special_tokens=True)
        result.append(tokenizer.apply_chat_template(
            [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}],
            tokenize=False, add_generation_prompt=True,
        ))
    return result


def run(root, name):
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, set_seed

    assert torch.cuda.is_available() and torch.cuda.device_count() == 1
    out = root / "outputs" / name
    out.mkdir(parents=True, exist_ok=False)
    info = json.loads((root / "outputs/data_manifest.json").read_text())
    train_path, test_path = root / "data/train.jsonl", root / "data/test.jsonl"
    assert sha(train_path) == info["train_sha256"] and sha(test_path) == info["test_sha256"]
    train_rows, test_rows = read_rows(train_path), read_rows(test_path)
    set_seed(SEED)
    torch.backends.cuda.matmul.allow_tf32 = True
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=info["model_revision"], local_files_only=True)
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, revision=info["model_revision"], dtype=torch.bfloat16,
        attn_implementation="sdpa", local_files_only=True, use_safetensors=True,
    ).to("cuda:0")
    base_parameters = sum(p.numel() for p in model.parameters())
    if name == "base":
        model.requires_grad_(False)
    elif name.startswith("lora"):
        model = get_peft_model(model, LoraConfig(task_type="CAUSAL_LM", bias="none", **RUNS[name]))
        assert all("lora_" in key for key, p in model.named_parameters() if p.requires_grad)
    else:
        assert all(p.requires_grad for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    lr = 2e-5 if name == "full" else 2e-4
    config = dict(
        model=MODEL, model_revision=info["model_revision"], run=name, lora=RUNS[name],
        seed=SEED, num_train_epochs=1, per_device_train_batch_size=16,
        gradient_accumulation_steps=1, learning_rate=lr if name != "base" else None,
        lr_scheduler_type="cosine", warmup_ratio=0.05, weight_decay=0.01,
        optim="adamw_torch_fused", bf16=True, attention="sdpa", text_tokens=TEXT_TOKENS,
        max_length=MAX_LENGTH, train_sha256=info["train_sha256"], test_sha256=info["test_sha256"],
        train_examples=len(train_rows), test_examples=len(test_rows),
        versions={package: importlib.metadata.version(package) for package in ("torch", "transformers", "peft", "datasets", "accelerate")},
        gpu=torch.cuda.get_device_properties(0).name,
        gpu_uuid=str(torch.cuda.get_device_properties(0).uuid),
    )
    write_json(out / "config.json", config)
    print(json.dumps(config, ensure_ascii=False), flush=True)
    seconds, peak, reserved, steps = 0.0, 0.0, 0.0, 0
    if name != "base":
        train = []
        for row, prompt in zip(train_rows, prompts(tokenizer, train_rows)):
            prefix = tokenizer.encode(prompt, add_special_tokens=False)
            answer = tokenizer.encode(str(row["label"]) + tokenizer.eos_token, add_special_tokens=False)
            ids = prefix + answer
            assert len(ids) <= MAX_LENGTH
            train.append(dict(input_ids=ids, labels=[-100] * len(prefix) + answer))

        def collate(examples):
            size = max(len(row["input_ids"]) for row in examples)
            ids = torch.full((len(examples), size), tokenizer.pad_token_id, dtype=torch.long)
            labels = torch.full_like(ids, -100)
            attention = torch.zeros_like(ids)
            for i, row in enumerate(examples):
                n = len(row["input_ids"])
                ids[i, :n] = torch.tensor(row["input_ids"])
                labels[i, :n] = torch.tensor(row["labels"])
                attention[i, :n] = 1
            return dict(input_ids=ids, attention_mask=attention, labels=labels)

        sample = collate(train[:2])
        for i, row in enumerate(train[:2]):
            keep = sample["labels"][i] != -100
            assert tokenizer.decode(sample["labels"][i][keep].tolist()) == str(train_rows[i]["label"]) + tokenizer.eos_token
            assert sample["labels"][i, len(row["input_ids"])-1].item() == tokenizer.eos_token_id
        model.config.use_cache = False
        trainer = Trainer(
            model=model,
            args=TrainingArguments(
                output_dir=str(root / "checkpoints" / name),
                num_train_epochs=1, per_device_train_batch_size=16,
                gradient_accumulation_steps=1, learning_rate=lr,
                lr_scheduler_type="cosine", warmup_ratio=0.05, weight_decay=0.01,
                optim="adamw_torch_fused", bf16=True, tf32=True,
                logging_steps=25, save_strategy="no", eval_strategy="no",
                report_to="none", seed=SEED, data_seed=SEED,
                dataloader_num_workers=0, disable_tqdm=True,
            ),
            train_dataset=train, data_collator=collate, processing_class=tokenizer,
        )
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        start = time.perf_counter()
        trainer.train()
        torch.cuda.synchronize()
        seconds = time.perf_counter() - start
        peak = torch.cuda.max_memory_allocated() / 2**30
        reserved = torch.cuda.max_memory_reserved() / 2**30
        steps = trainer.state.global_step
        assert steps == 625
        write_json(out / "training_history.json", trainer.state.log_history)
        trainer.save_model()
        # Free optimizer state before generation; timing/peak above are training-only.
        del trainer
        import gc
        gc.collect()
        torch.cuda.empty_cache()

    model.config.use_cache = True
    model.eval()
    tokenizer.padding_side = "left"
    predictions = []
    test_prompts = prompts(tokenizer, test_rows)
    for start in range(0, len(test_rows), 32):
        batch_rows = test_rows[start:start+32]
        inputs = tokenizer(test_prompts[start:start+32], padding=True, return_tensors="pt", add_special_tokens=False).to("cuda:0")
        with torch.inference_mode():
            result = model.generate(
                **inputs, max_new_tokens=4, do_sample=False,
                eos_token_id=tokenizer.eos_token_id, pad_token_id=tokenizer.pad_token_id,
                use_cache=True,
            )
        outputs = tokenizer.batch_decode(result[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        for row, output in zip(batch_rows, outputs):
            output = output.strip()
            predicted = int(output) if re.fullmatch("[0-5]", output) else -1
            predictions.append(dict(id=row["id"], label=row["label"], predicted=predicted, output=output))
        if start % 320 == 0:
            print(f"eval {name}: {len(predictions)}/{len(test_rows)}", flush=True)
    write_rows(out / "predictions.jsonl", predictions)
    result = dict(
        run=name, **metrics([r["label"] for r in predictions], [r["predicted"] for r in predictions]),
        base_parameters=base_parameters, trainable_parameters=trainable,
        trainable_percent=100 * trainable / base_parameters,
        train_seconds=seconds, peak_allocated_gib=peak, peak_reserved_gib=reserved,
        optimizer_steps=steps, train_examples=len(train_rows) if name != "base" else 0,
        test_examples=len(test_rows), train_sha256=info["train_sha256"], test_sha256=info["test_sha256"],
    )
    write_json(out / "metrics.json", result)
    print("RESULT", json.dumps(result, ensure_ascii=False), flush=True)


def summarize(root):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = [json.loads((root / "outputs" / name / "metrics.json").read_text()) for name in RUNS]
    fields = [key for key in rows[0] if key != "per_class_f1"]
    with (root / "outputs/metrics.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: v for k, v in row.items() if k in fields} for row in rows)
    info = json.loads((root / "outputs/data_manifest.json").read_text())
    test = {row["id"]: row for row in read_rows(root / "data/test.jsonl")}
    predictions = {name: {row["id"]: row for row in read_rows(root / "outputs" / name / "predictions.jsonl")} for name in ("base", "full", "lora")}
    with (root / "outputs/manual_examples.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "text", "gold", "base", "full", "lora"])
        writer.writeheader()
        for i in info["manual_ids"]:
            row = dict(id=i, text=test[i]["text"], gold=LABELS[test[i]["label"]])
            for name in predictions:
                pred = predictions[name][i]["predicted"]
                row[name] = LABELS[pred] if pred >= 0 else "INVALID"
            writer.writerow(row)
    plt.figure(figsize=(8, 3.5))
    for name in ("full", "lora"):
        history = json.loads((root / "outputs" / name / "training_history.json").read_text())
        points = [p for p in history if "loss" in p]
        plt.plot([p["step"] for p in points], [p["loss"] for p in points], label=name)
    plt.xlabel("optimizer step")
    plt.ylabel("assistant-only training loss")
    plt.legend()
    plt.grid(alpha=.3)
    plt.tight_layout()
    plt.savefig(root / "outputs/loss.png", dpi=140)
    print((root / "outputs/metrics.csv").read_text())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--run", choices=list(RUNS))
    parser.add_argument("--summarize", action="store_true")
    parser.add_argument("--work-dir", type=Path, help="Fresh experiment directory; prevents overwriting delivered results")
    args = parser.parse_args()
    root = args.work_dir.resolve() if args.work_dir else Path(__file__).resolve().parent
    if args.prepare:
        prepare(root)
    elif args.run:
        run(root, args.run)
    elif args.summarize:
        summarize(root)
    else:
        parser.error("choose --prepare, --run or --summarize")
