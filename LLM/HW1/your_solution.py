import argparse
import json
import math
import os
import time
from pathlib import Path

import torch
from datasets import Features, Sequence, Value, load_dataset
from torch.optim.lr_scheduler import LambdaLR
from transformers import (
    AutoTokenizer,
    Qwen3Config,
    Qwen3ForCausalLM,
    Trainer,
    TrainerCallback,
    TrainingArguments,
    default_data_collator,
    set_seed,
)


# Required assignment constants.
MAX_TRAINING_TIME_SECONDS = 60 * 15
MAX_LENGTH = 512
INPUT_IDS = "input_ids"
ATTENTION_MASK = "attention_mask"
LABELS = "labels"

TOKENIZER_NAME = "ai-forever/rugpt3small_based_on_gpt2"
OUTPUT_DIR = "./output_dir"
TOKENIZED_DIR = "./tokenized_data"
NUM_SHARDS = 32
VALIDATION_SIZE = 5000


TRAINING_CONFIG = {
    "output_dir": f"{OUTPUT_DIR}/final",
    "optim": "adamw_torch_fused",
    "num_train_epochs": 1,
    "per_device_train_batch_size": 16,
    "per_device_eval_batch_size": 32,
    "gradient_accumulation_steps": 1,
    "learning_rate": 1e-3,
    "weight_decay": 0.1,
    "adam_beta1": 0.9,
    "adam_beta2": 0.95,
    "max_grad_norm": 1.0,
    "warmup_steps": 100,
    "logging_steps": 5,
    "eval_strategy": "no",
    "save_strategy": "no",
    "save_only_model": True,
    "bf16": True,
    "tf32": True,
    "gradient_checkpointing": False,
    "dataloader_num_workers": 4,
    "dataloader_pin_memory": True,
    "dataloader_drop_last": True,
    "torch_compile": True,
    "report_to": "none",
    "seed": 42,
}

EXPERIMENT_CONFIG = {
    # Unlike stock HF schedulers, this schedule spans the actual wall-clock
    # budget rather than the much longer complete Wikipedia epoch.
    "time_scheduler": "cosine",  # cosine | linear | constant
    "min_lr_ratio": 0.05,
    "eval_subset_size": 500,
    "eval_every_seconds": 180,
    "generate_after_training": True,
    "full_eval": True,
    "save_model": True,
    "save_on_timeout": True,
    "fp32_master_weights": False,
}

GENERATION_PROMPTS = [
    "Москва — столица",
    "Александр Сергеевич Пушкин родился",
    "Математика — это",
    "В 1812 году",
    "Река Волга",
]


class TimeoutCallback(TrainerCallback):
    """Stop training after the assignment's wall-clock budget."""

    def __init__(self, timeout_seconds, save_on_timeout=True):
        self.timeout_seconds = timeout_seconds
        self.save_on_timeout = save_on_timeout
        self.start_time = None

    def on_train_begin(self, args, state, control, **kwargs):
        self.start_time = time.monotonic()

    def on_step_end(self, args, state, control, **kwargs):
        if self.start_time is not None:
            elapsed = time.monotonic() - self.start_time
            if elapsed > self.timeout_seconds:
                control.should_training_stop = True
                control.should_evaluate = True
                control.should_save = self.save_on_timeout
                print(f"Training stopped after {elapsed:.2f} seconds")
        return control


class PeriodicEvalCallback(TrainerCallback):
    """Request validation at comparable wall-clock moments."""

    def __init__(self, every_seconds):
        self.every_seconds = every_seconds
        self.next_eval = None

    def on_train_begin(self, args, state, control, **kwargs):
        self.next_eval = time.monotonic() + self.every_seconds

    def on_step_end(self, args, state, control, **kwargs):
        if self.next_eval is not None and time.monotonic() >= self.next_eval:
            control.should_evaluate = True
            self.next_eval = time.monotonic() + self.every_seconds
        return control


class WallClockTrainer(Trainer):
    """Trainer with a wall-clock LR schedule and time/token logging."""

    def __init__(self, *args, time_budget, time_scheduler, min_lr_ratio, **kwargs):
        super().__init__(*args, **kwargs)
        self.time_budget = time_budget
        self.time_scheduler = time_scheduler
        self.min_lr_ratio = min_lr_ratio
        self.train_started_at = None
        self.tokens_seen = 0

    def elapsed(self):
        if self.train_started_at is None:
            return 0.0
        return time.monotonic() - self.train_started_at

    def train(self, *args, **kwargs):
        self.train_started_at = time.monotonic()
        return super().train(*args, **kwargs)

    def _lr_multiplier(self, step):
        if step < self.args.warmup_steps:
            return (step + 1) / max(1, self.args.warmup_steps)
        progress = min(1.0, self.elapsed() / self.time_budget)
        if self.time_scheduler == "constant":
            value = 1.0
        elif self.time_scheduler == "linear":
            value = 1.0 - progress
        elif self.time_scheduler == "cosine":
            value = 0.5 * (1.0 + math.cos(math.pi * progress))
        else:
            raise ValueError(f"Unknown time scheduler: {self.time_scheduler}")
        return self.min_lr_ratio + (1.0 - self.min_lr_ratio) * value

    def create_scheduler(self, num_training_steps, optimizer=None):
        if self.lr_scheduler is None:
            optimizer = optimizer if optimizer is not None else self.optimizer
            self.lr_scheduler = LambdaLR(optimizer, self._lr_multiplier)
            self._created_lr_scheduler = True
        return self.lr_scheduler

    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        if model.training:
            # Count all fixed block positions without synchronizing GPU -> CPU each step.
            self.tokens_seen += inputs[INPUT_IDS].numel()
        return super().compute_loss(
            model,
            inputs,
            return_outputs=return_outputs,
            num_items_in_batch=num_items_in_batch,
        )

    def log(self, logs, start_time=None):
        logs["elapsed_sec"] = round(self.elapsed(), 1)
        logs["train_tokens"] = self.tokens_seen
        super().log(logs, start_time)


def prepare_tokenizer():
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)
    tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def tokenize_function(examples, tokenizer):
    tokenized = tokenizer(
        examples["text"],
        truncation=True,
        padding="max_length",
        max_length=MAX_LENGTH,
    )
    # Follow the provided skeleton literally: labels are a copy of input_ids.
    tokenized[LABELS] = [ids.copy() for ids in tokenized[INPUT_IDS]]
    return {
        LABELS: tokenized[LABELS],
        INPUT_IDS: tokenized[INPUT_IDS],
        ATTENTION_MASK: tokenized[ATTENTION_MASK],
    }


def save_as_parquets(dataset, output_dir=TOKENIZED_DIR, num_shards=NUM_SHARDS):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    for index in range(num_shards):
        shard_path = output_path / f"{index:05d}.parquet"
        dataset.shard(num_shards=num_shards, index=index, contiguous=True).to_parquet(shard_path)


def prepare_dataset():
    dataset = load_dataset("wikimedia/wikipedia", "20231101.ru", split="train")
    tokenizer = prepare_tokenizer()
    features = Features(
        {
            INPUT_IDS: Sequence(Value("int32")),
            ATTENTION_MASK: Sequence(Value("int8")),
            LABELS: Sequence(Value("int32")),
        }
    )
    tokenized = dataset.map(
        tokenize_function,
        fn_kwargs={"tokenizer": tokenizer},
        batched=True,
        num_proc=min(24, os.cpu_count() or 1),
        remove_columns=dataset.column_names,
        features=features,
        desc="Tokenizing Russian Wikipedia",
    )
    save_as_parquets(tokenized)
    print(f"Saved {len(tokenized):,} samples to {TOKENIZED_DIR} in {NUM_SHARDS} shards")


def load_tokenized_dataset(data_dir=TOKENIZED_DIR):
    files = sorted(str(path) for path in Path(data_dir).glob("*.parquet"))
    if len(files) != NUM_SHARDS:
        raise FileNotFoundError(
            f"Expected {NUM_SHARDS} parquet shards in {data_dir}, found {len(files)}. "
            "Run `python your_solution.py prepare` first."
        )
    return load_dataset("parquet", data_files=files, split="train")


def split_dataset(dataset, validation_size=VALIDATION_SIZE):
    if len(dataset) <= validation_size:
        raise ValueError("Dataset is smaller than the required validation split")
    eval_dataset = dataset.select(range(validation_size))
    train_dataset = dataset.select(range(validation_size, len(dataset)))
    print(f"Training samples: {len(train_dataset):,}")
    print(f"Validation samples: {len(eval_dataset):,}")
    return train_dataset, eval_dataset


def create_model(tokenizer):
    # Architecture from the assignment; do not change.
    model_config = {
        "hidden_size": 2048,
        "num_hidden_layers": 12,
        "num_attention_heads": 16,
        "num_key_value_heads": 8,
        "intermediate_size": 8192,
        "head_dim": 128,
        "hidden_act": "silu",
        "initializer_range": 0.02,
        "scale_attn_weights": True,
        "use_cache": True,
    }
    config = Qwen3Config(
        vocab_size=tokenizer.vocab_size,
        bos_token_id=tokenizer.bos_token_id,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id,
        **model_config,
    )
    model = Qwen3ForCausalLM._from_config(
        config,
        attn_implementation="flash_attention_2",
        torch_dtype=torch.bfloat16,
    )
    total_params = sum(parameter.numel() for parameter in model.parameters())
    print(f"Total parameters: {total_params:,}")
    print(f"Model pad token id: {model.config.pad_token_id}")
    return model


def parse_value(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def parse_overrides(pairs):
    overrides = {}
    for pair in pairs:
        key, separator, raw = pair.partition("=")
        if not separator:
            raise ValueError(f"Override must be key=value, got: {pair}")
        overrides[key] = parse_value(raw)
    return overrides


@torch.no_grad()
def generate_samples(model, tokenizer, prompts=GENERATION_PROMPTS):
    model.eval()
    model.config.use_cache = True
    device = next(model.parameters()).device
    generations = []
    modes = {
        "greedy": {"do_sample": False},
        "sampling": {"do_sample": True, "temperature": 0.8, "top_p": 0.95, "top_k": 50},
    }
    for prompt in prompts:
        encoded = tokenizer(prompt, return_tensors="pt").to(device)
        for mode, kwargs in modes.items():
            torch.manual_seed(42)
            output = model.generate(
                **encoded,
                max_new_tokens=64,
                min_new_tokens=16,
                repetition_penalty=1.15,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                **kwargs,
            )
            text = tokenizer.decode(output[0], skip_special_tokens=True)
            record = {"prompt": prompt, "mode": mode, "text": text}
            generations.append(record)
            print(f"[{mode}] {text}\n")
    return generations


def train_model(run_name, overrides, time_budget=MAX_TRAINING_TIME_SECONDS, max_steps=None):
    set_seed(42)
    training_config = dict(TRAINING_CONFIG)
    experiment_config = dict(EXPERIMENT_CONFIG)
    training_config["output_dir"] = f"{OUTPUT_DIR}/runs/{run_name}"
    training_config["run_name"] = run_name
    for key, value in overrides.items():
        if key in experiment_config:
            experiment_config[key] = value
        else:
            training_config[key] = value
    if max_steps is not None:
        training_config["max_steps"] = max_steps

    print("Training config:", json.dumps(training_config, ensure_ascii=False, indent=2))
    print("Experiment config:", json.dumps(experiment_config, ensure_ascii=False, indent=2))
    tokenizer = prepare_tokenizer()
    train_dataset, eval_dataset = split_dataset(load_tokenized_dataset())
    subset_size = min(experiment_config["eval_subset_size"], len(eval_dataset))
    eval_subset = eval_dataset.select(range(subset_size))

    model = create_model(tokenizer)
    if experiment_config["fp32_master_weights"]:
        # Keep FP32 parameters/optimizer state while TrainingArguments.bf16
        # provides BF16 autocast for matrix multiplications.
        model = model.float()
    model.config.use_cache = False
    callbacks = [TimeoutCallback(
        timeout_seconds=time_budget,
        save_on_timeout=experiment_config["save_on_timeout"],
    )]
    if experiment_config["eval_every_seconds"] > 0:
        callbacks.append(PeriodicEvalCallback(experiment_config["eval_every_seconds"]))
    trainer = WallClockTrainer(
        model=model,
        args=TrainingArguments(**training_config),
        train_dataset=train_dataset,
        eval_dataset=eval_subset,
        data_collator=default_data_collator,
        callbacks=callbacks,
        time_budget=time_budget,
        time_scheduler=experiment_config["time_scheduler"],
        min_lr_ratio=experiment_config["min_lr_ratio"],
    )

    train_result = trainer.train()
    train_seconds = trainer.elapsed()
    final_eval_dataset = eval_dataset if experiment_config["full_eval"] else eval_subset
    print(f"Running final evaluation on {len(final_eval_dataset)} validation samples...")
    eval_results = trainer.evaluate(eval_dataset=final_eval_dataset, metric_key_prefix="eval")
    print("Final evaluation results:", eval_results)
    trainer.save_state()

    if experiment_config["save_model"]:
        final_dir = Path(training_config["output_dir"]) / "model"
        trainer.model.config.use_cache = True
        trainer.save_model(final_dir)
        tokenizer.save_pretrained(final_dir)

    eval_loss = float(eval_results["eval_loss"])
    summary = {
        "run_name": run_name,
        "training_config": training_config,
        "experiment_config": experiment_config,
        "time_budget_seconds": time_budget,
        "train_seconds": train_seconds,
        "global_step": trainer.state.global_step,
        "train_tokens": trainer.tokens_seen,
        "train_tokens_per_second": trainer.tokens_seen / max(train_seconds, 1e-9),
        "train_loss": train_result.training_loss,
        "eval_loss": eval_loss,
        "perplexity": math.exp(eval_loss) if math.isfinite(eval_loss) and eval_loss < 100 else None,
        "peak_gpu_memory_gb": torch.cuda.max_memory_allocated() / 2**30,
        "generations": [],
    }
    summary_path = Path(training_config["output_dir"]) / "run_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    if experiment_config["generate_after_training"] and math.isfinite(eval_loss):
        summary["generations"] = generate_samples(trainer.model, tokenizer)
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "train"])
    parser.add_argument("--name", default="final")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    parser.add_argument("--time-budget", type=int, default=MAX_TRAINING_TIME_SECONDS)
    parser.add_argument("--max-steps", type=int)
    args = parser.parse_args()

    if args.command == "prepare":
        prepare_dataset()
    else:
        train_model(
            run_name=args.name,
            overrides=parse_overrides(args.set),
            time_budget=args.time_budget,
            max_steps=args.max_steps,
        )


if __name__ == "__main__":
    main()
