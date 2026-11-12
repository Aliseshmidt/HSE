"""Merge language-only LoRA into the specified original full checkpoint."""

import argparse
import json
from pathlib import Path

from prepare_data import MODEL, REVISION
from train_rl import fingerprint


def main():
    import torch
    from peft import PeftModel
    from transformers import AutoModelForImageTextToText, AutoTokenizer

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    run = root / "runs" / args.name
    record = json.loads((run / "config.json").read_text())
    output = root / "checkpoints" / args.name
    output.mkdir(parents=True, exist_ok=False)
    base = AutoModelForImageTextToText.from_pretrained(
        MODEL, revision=REVISION, dtype=torch.bfloat16
    )
    model = PeftModel.from_pretrained(base, run / "adapter")
    merged = model.merge_and_unload()
    assert not any("lora_" in n for n, _ in merged.named_parameters())
    merged.save_pretrained(output, safe_serialization=True, max_shard_size="5GB")
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
    assert fingerprint(tokenizer) == record["tokenizer_fingerprint"]
    tokenizer.save_pretrained(output)
    (output / "export_provenance.json").write_text(
        json.dumps(
            dict(base=MODEL, revision=REVISION, run=args.name, merged=True), indent=2
        )
        + "\n"
    )
    print("MERGED", output, flush=True)


if __name__ == "__main__":
    main()
