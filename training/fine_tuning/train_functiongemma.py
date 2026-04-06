#!/usr/bin/env python3
"""
Fine-tune FunctionGemma for NWO Robotics
Uses HuggingFace Transformers and PEFT for efficient fine-tuning
"""

import torch
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset
import wandb


@dataclass
class TrainingConfig:
    """Training configuration"""
    model_name: str = "google/gemma-2b-it"  # Base model
    output_dir: str = "./functiongemma-nwo"
    train_file: str = "./datasets/nwo_commands_train.jsonl"
    val_file: str = "./datasets/nwo_commands_val.jsonl"
    
    # LoRA config
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    
    # Training config
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    num_epochs: int = 3
    learning_rate: float = 2e-4
    max_seq_length: int = 512
    
    # Optimization
    warmup_steps: int = 100
    logging_steps: int = 10
    save_steps: int = 500
    eval_steps: int = 500
    
    # Hardware
    use_fp16: bool = True
    use_gradient_checkpointing: bool = True


def load_dataset(train_file: str, val_file: str) -> tuple:
    """Load training and validation datasets"""
    
    def load_jsonl(path: str) -> List[Dict]:
        data = []
        with open(path, 'r') as f:
            for line in f:
                data.append(json.loads(line))
        return data
    
    train_data = load_jsonl(train_file)
    val_data = load_jsonl(val_file)
    
    return train_data, val_data


def format_for_training(example: Dict) -> str:
    """Format a conversation example for training"""
    messages = example.get('messages', [])
    
    formatted = ""
    for msg in messages:
        role = msg.get('role', '')
        content = msg.get('content', '')
        
        if role == 'system':
            formatted += f"<start_of_turn>system\n{content}<end_of_turn>\n"
        elif role == 'user':
            formatted += f"<start_of_turn>user\n{content}<end_of_turn>\n"
        elif role == 'assistant':
            formatted += f"<start_of_turn>model\n{content}<end_of_turn>\n"
    
    return formatted


def prepare_dataset(data: List[Dict], tokenizer, max_length: int = 512):
    """Prepare dataset for training"""
    
    formatted_texts = [format_for_training(ex) for ex in data]
    
    # Tokenize
    tokenized = tokenizer(
        formatted_texts,
        truncation=True,
        max_length=max_length,
        padding=False,
        return_tensors=None
    )
    
    # Create labels (same as input_ids for causal LM)
    tokenized['labels'] = tokenized['input_ids'].copy()
    
    return Dataset.from_dict(tokenized)


def setup_lora_model(model, config: TrainingConfig):
    """Setup LoRA adapters for efficient fine-tuning"""
    
    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_dropout=config.lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    return model


def train(config: TrainingConfig):
    """Main training function"""
    
    print(f"Loading model: {config.model_name}")
    
    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(config.model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        config.model_name,
        torch_dtype=torch.float16 if config.use_fp16 else torch.float32,
        device_map="auto",
        trust_remote_code=True
    )
    
    # Setup LoRA
    model = setup_lora_model(model, config)
    
    # Enable gradient checkpointing
    if config.use_gradient_checkpointing:
        model.enable_input_require_grads()
        model.gradient_checkpointing_enable()
    
    # Load datasets
    print("Loading datasets...")
    train_data, val_data = load_dataset(config.train_file, config.val_file)
    train_dataset = prepare_dataset(train_data, tokenizer, config.max_seq_length)
    val_dataset = prepare_dataset(val_data, tokenizer, config.max_seq_length)
    
    print(f"Train samples: {len(train_dataset)}")
    print(f"Val samples: {len(val_dataset)}")
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=config.output_dir,
        num_train_epochs=config.num_epochs,
        per_device_train_batch_size=config.batch_size,
        per_device_eval_batch_size=config.batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        warmup_steps=config.warmup_steps,
        logging_steps=config.logging_steps,
        save_steps=config.save_steps,
        eval_steps=config.eval_steps,
        evaluation_strategy="steps",
        save_strategy="steps",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        fp16=config.use_fp16,
        report_to="wandb" if wandb.run else None,
        remove_unused_columns=False,
    )
    
    # Data collator
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True,
        return_tensors="pt"
    )
    
    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
    )
    
    # Train
    print("Starting training...")
    trainer.train()
    
    # Save final model
    print(f"Saving model to {config.output_dir}")
    trainer.save_model(config.output_dir)
    tokenizer.save_pretrained(config.output_dir)
    
    # Merge LoRA weights for deployment
    print("Merging LoRA weights...")
    merged_model = model.merge_and_unload()
    merged_output = Path(config.output_dir) / "merged"
    merged_model.save_pretrained(merged_output)
    tokenizer.save_pretrained(merged_output)
    
    print("Training complete!")
    print(f"Model saved to: {config.output_dir}")
    print(f"Merged model saved to: {merged_output}")


def main():
    parser = argparse.ArgumentParser(description='Fine-tune FunctionGemma for NWO Robotics')
    parser.add_argument('--model', default='google/gemma-2b-it', help='Base model name')
    parser.add_argument('--output', default='./functiongemma-nwo', help='Output directory')
    parser.add_argument('--train', default='./datasets/nwo_commands_train.jsonl', help='Training data')
    parser.add_argument('--val', default='./datasets/nwo_commands_val.jsonl', help='Validation data')
    parser.add_argument('--epochs', type=int, default=3, help='Number of epochs')
    parser.add_argument('--batch-size', type=int, default=4, help='Batch size')
    parser.add_argument('--lr', type=float, default=2e-4, help='Learning rate')
    parser.add_argument('--wandb', action='store_true', help='Enable W&B logging')
    args = parser.parse_args()
    
    # Initialize W&B if requested
    if args.wandb:
        wandb.init(project="functiongemma-nwo", name="nwo-robotics-v1")
    
    config = TrainingConfig(
        model_name=args.model,
        output_dir=args.output,
        train_file=args.train,
        val_file=args.val,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr
    )
    
    train(config)


if __name__ == '__main__':
    main()
