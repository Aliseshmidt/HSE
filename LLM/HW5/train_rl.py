"""TRL GRPO only. Gold responses are reward inputs, never supervised labels."""

import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import time

from prepare_data import MODEL, REVISION, SEED
from rewards import make_reward

CONFIGS = {
    "rl1_exact": dict(
        loss_type="grpo", scale_rewards="group", reward_weights=[1.0, 0.0]
    ),
    "rl2_dense": dict(
        loss_type="grpo", scale_rewards="group", reward_weights=[0.0, 1.0]
    ),
    "rl3_drgrpo": dict(
        loss_type="dr_grpo", scale_rewards="none", reward_weights=[0.0, 1.0]
    ),
}


def fingerprint(tokenizer):
    return hashlib.sha256(
        json.dumps(
            dict(
                vocab=tokenizer.get_vocab(),
                template=tokenizer.chat_template,
                special=tokenizer.special_tokens_map,
            ),
            sort_keys=True,
            ensure_ascii=False,
        ).encode()
    ).hexdigest()


def main():
    import torch
    from datasets import load_dataset
    from huggingface_hub import snapshot_download
    from peft import LoraConfig
    from transformers import (
        AutoModelForImageTextToText,
        AutoTokenizer,
        TrainerCallback,
        set_seed,
    )
    from trl import GRPOConfig, GRPOTrainer

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", choices=list(CONFIGS), required=True)
    parser.add_argument("--steps", type=int, default=16)
    parser.add_argument("--validation-size", type=int, default=32)
    parser.add_argument(
        "--name", help="Unique output name (use pilot for a smoke check)"
    )
    parser.add_argument("--skip-validation", action="store_true")
    parser.add_argument(
        "--no-vllm",
        action="store_true",
        help="Slow Transformers fallback for diagnostics",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    name = args.name or args.config
    out = root / "runs" / name
    out.mkdir(parents=True, exist_ok=False)
    assert torch.cuda.device_count() == 1
    set_seed(SEED)
    snapshot = snapshot_download(MODEL, revision=REVISION)
    tokenizer = AutoTokenizer.from_pretrained(snapshot)
    original = fingerprint(tokenizer)
    tokenizer.padding_side = "left"
    dataset = load_dataset(
        "json",
        data_files={
            s: str(root / "data" / (s + ".jsonl")) for s in ("train", "validation")
        },
    )
    assert not set(dataset["train"]["dialog_id"]) & set(
        dataset["validation"]["dialog_id"]
    )
    assert "labels" not in dataset["train"].column_names
    config = GRPOConfig(
        output_dir=str(out / "adapter"),
        max_steps=args.steps,
        learning_rate=1e-5,
        lr_scheduler_type="constant_with_warmup",
        warmup_steps=2,
        weight_decay=0.0,
        max_grad_norm=1.0,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        per_device_eval_batch_size=4,
        num_generations=4,
        max_completion_length=512,
        temperature=0.8,
        top_p=0.95,
        top_k=0,
        beta=0.01,
        num_iterations=1,
        epsilon=0.2,
        bf16=True,
        tf32=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        use_vllm=not args.no_vllm,
        vllm_mode="colocate",
        vllm_gpu_memory_utilization=0.35,
        vllm_max_model_length=2048,
        vllm_enable_sleep_mode=True,
        use_cache=True,
        remove_unused_columns=False,
        mask_truncated_completions=True,
        logging_steps=1,
        logging_nan_inf_filter=False,
        report_to="none",
        save_strategy="no",
        eval_strategy="no",
        disable_tqdm=True,
        seed=SEED,
        data_seed=SEED,
        push_to_hub=False,
        **CONFIGS[args.config],
    )
    # MLP-only adapters avoid changing the vision encoder and cover every language layer.
    peft = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.0,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=r".*language_model\.layers\.\d+\.mlp\.(gate_proj|up_proj|down_proj)$",
    )
    record = dict(
        name=name,
        config=args.config,
        grpo=config.to_dict(),
        lora=peft.to_dict(),
        model=MODEL,
        revision=REVISION,
        tokenizer_fingerprint=original,
        validation_used=0
        if args.skip_validation
        else min(args.validation_size, len(dataset["validation"])),
        versions={
            p: version(p) for p in ("torch", "transformers", "trl", "peft", "datasets")
        },
        gpu=str(torch.cuda.get_device_properties(0).uuid),
        train_sha256=hashlib.sha256(
            (root / "data/train.jsonl").read_bytes()
        ).hexdigest(),
        validation_sha256=hashlib.sha256(
            (root / "data/validation.jsonl").read_bytes()
        ).hexdigest(),
    )
    (out / "config.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2, default=str) + "\n"
    )

    class Trace(TrainerCallback):
        def on_log(self, arguments, state, control, logs=None, **kwargs):
            if logs:
                item = dict(step=state.global_step, **logs)
                with (out / "trace.jsonl").open("a") as f:
                    f.write(json.dumps(item, default=str) + "\n")

    if not args.no_vllm:
        # TRL 1.16 has no language_model_only flag. Use the same supported vLLM
        # text-only option as evaluate.py, without editing either library/evaluator.
        import trl.generation.vllm_generation as vg

        class TextOnlyLLM(vg.LLM):
            def __init__(self, *a, **kw):
                kw.setdefault("language_model_only", True)
                kw.setdefault("enforce_eager", True)
                super().__init__(*a, **kw)

        vg.LLM = TextOnlyLLM
    model = AutoModelForImageTextToText.from_pretrained(
        snapshot, dtype=torch.bfloat16, attn_implementation="sdpa"
    )
    trainer = GRPOTrainer(
        model=model,
        args=config,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"].select(
            range(min(args.validation_size, len(dataset["validation"])))
        ),
        reward_funcs=[make_reward("exact"), make_reward("dense")],
        processing_class=tokenizer,
        peft_config=peft,
        callbacks=[Trace()],
    )
    assert fingerprint(tokenizer) == original, "Tokenizer was changed"
    trainable = [
        (n, p.numel()) for n, p in trainer.model.named_parameters() if p.requires_grad
    ]
    assert trainable and all(
        "lora_" in n and "language_model" in n for n, _ in trainable
    )
    print("TRAINABLE", sum(n for _, n in trainable), flush=True)
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    start = time.perf_counter()
    result = trainer.train()
    torch.cuda.synchronize()
    summary = dict(
        seconds=time.perf_counter() - start,
        optimizer_steps=trainer.state.global_step,
        peak_allocated_gib=torch.cuda.max_memory_allocated() / 2**30,
        peak_reserved_gib=torch.cuda.max_memory_reserved() / 2**30,
        trainable_parameters=sum(n for _, n in trainable),
        metrics=result.metrics,
    )
    trainer.save_model(str(out / "adapter"))
    if not args.skip_validation:
        summary["validation"] = trainer.evaluate()
    assert fingerprint(tokenizer) == original
    (out / "history.json").write_text(
        json.dumps(trainer.state.log_history, indent=2, default=str) + "\n"
    )
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print("SUMMARY", json.dumps(summary, default=str), flush=True)


if __name__ == "__main__":
    main()
