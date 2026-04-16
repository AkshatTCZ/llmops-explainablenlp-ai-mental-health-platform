

from datasets import load_from_disk
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding
)
from transformers.trainer_utils import get_last_checkpoint
import os
import torch

def compute_metrics(eval_pred):
    """
    Compute metrics for evaluation.
    """
    import numpy as np
    from sklearn.metrics import accuracy_score, f1_score
    
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    
    accuracy = accuracy_score(labels, predictions)
    f1 = f1_score(labels, predictions, average='weighted')
    
    return {
        'accuracy': accuracy,
        'f1': f1
    }

def main():
    # Load processed dataset - check multiple possible locations
    possible_paths = [
        "./data/go_emotions_processed",
        "data/go_emotions_processed",
        "data/processed_go_emotions",
        "./data/processed_go_emotions"
    ]
    
    dataset_path = None
    for path in possible_paths:
        if os.path.exists(path):
            dataset_path = path
            break
    
    if dataset_path is None:
        raise FileNotFoundError(
            f"Processed dataset not found in any of these locations: {possible_paths}. "
            "Please run scripts/preprocess.py first."
        )
    
    print(f"Loading processed dataset from {dataset_path}...")
    
    dataset = load_from_disk(dataset_path)
    print(f"Dataset loaded successfully!")
    print(f"  Splits: {list(dataset.keys())}")
    print(f"  Train size: {len(dataset['train'])}")
    if 'validation' in dataset:
        print(f"  Validation size: {len(dataset['validation'])}")
    if 'test' in dataset:
        print(f"  Test size: {len(dataset['test'])}")
    
    # Show example
    print(f"\nExample from training set:")
    example = dataset['train'][0]
    for key in example.keys():
        if key in ['input_ids', 'attention_mask']:
            print(f"  {key}: shape/length = {len(example[key])}")
        else:
            print(f"  {key}: {example[key]}")
    
    # Load model and tokenizer
    model_name = "distilbert-base-uncased"
    num_labels = 28
    
    print(f"\nLoading tokenizer from {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    print(f"Loading model from {model_name}...")
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=num_labels
    )
    
    print(f"Model configured for {num_labels} labels")
    
    # Set up training arguments
    output_dir = "./model"
    os.makedirs(output_dir, exist_ok=True)
    
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=10,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        learning_rate=2e-5,
        weight_decay=0.01,
        logging_dir=f"{output_dir}/logs",
        logging_steps=100,
        eval_strategy="epoch" if 'validation' in dataset else "no",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True if 'validation' in dataset else False,
        metric_for_best_model="f1" if 'validation' in dataset else None,
        warmup_steps=500,
        fp16=torch.cuda.is_available(),  # Use mixed precision if GPU available
        report_to="none",  # Disable wandb/tensorboard unless needed
    )
    
    # Data collator
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset['train'],
        eval_dataset=dataset.get('validation', None),
        data_collator=data_collator,
        compute_metrics=compute_metrics if 'validation' in dataset else None,
    )
    
    # Check for existing checkpoint
    checkpoint = None
    if training_args.resume_from_checkpoint is not None:
        checkpoint = training_args.resume_from_checkpoint
    elif os.path.isdir(training_args.output_dir) and training_args.do_train:
        checkpoint = get_last_checkpoint(training_args.output_dir)
        if checkpoint is None and len(os.listdir(training_args.output_dir)) > 0:
            checkpoint = training_args.output_dir
    
    # Train
    print("\n" + "="*60)
    print("Starting training...")
    print("="*60)
    
    train_result = trainer.train(resume_from_checkpoint=checkpoint)
    
    # Save the final model and tokenizer
    print(f"\nSaving model and tokenizer to {output_dir}...")
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
    # Save training metrics
    trainer.save_state()
    
    print(f"\n✓ Training completed!")
    print(f"✓ Model and tokenizer saved to {output_dir}")
    
    # Print training summary
    print("\n" + "="*60)
    print("Training Summary:")
    print("="*60)
    print(f"  Total training steps: {train_result.global_step}")
    print(f"  Training loss: {train_result.training_loss:.4f}")
    if train_result.metrics:
        for key, value in train_result.metrics.items():
            print(f"  {key}: {value:.4f}")
    
    # Evaluate on test set if available
    if 'test' in dataset:
        print("\n" + "="*60)
        print("Evaluating on test set...")
        print("="*60)
        test_results = trainer.evaluate(eval_dataset=dataset['test'])
        print("Test set results:")
        for key, value in test_results.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")

if __name__ == "__main__":
    main()

