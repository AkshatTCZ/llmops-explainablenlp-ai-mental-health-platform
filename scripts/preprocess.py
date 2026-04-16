"""
Script to preprocess the go_emotions dataset.
Converts multi-label labels to single integer labels, tokenizes text,
and saves the processed dataset to disk.
"""

from datasets import load_dataset
from transformers import AutoTokenizer
import os

def convert_labels_to_single(example, label_names):
    """
    Convert multi-label labels to a single integer label.
    Uses the first label if available, otherwise uses 'neutral' if empty.
    """
    labels = example['labels']
    
    if len(labels) > 0:
        # Use the first label
        single_label = labels[0]
    else:
        # Find 'neutral' label index, or use 0 if not found
        try:
            neutral_idx = label_names.index('neutral')
            single_label = neutral_idx
        except ValueError:
            # If 'neutral' doesn't exist, use 0 as default
            single_label = 0
    
    return {'label': single_label}

def tokenize_text(examples, tokenizer):
    """
    Tokenize the text using the provided tokenizer.
    """
    return tokenizer(
        examples['text'],
        truncation=True,
        padding='max_length',
        max_length=128,
        return_tensors=None  # Return lists, not tensors
    )

def main():
    print("Loading go_emotions dataset...")
    dataset = load_dataset("go_emotions", "simplified")
    
    print("\nLoading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    
    # Get label names for neutral label lookup
    label_names = dataset['train'].features['labels'].feature.names
    print(f"\nFound {len(label_names)} labels")
    
    # Check if 'neutral' exists in labels
    if 'neutral' in label_names:
        print("'neutral' label found in dataset")
    else:
        print("'neutral' label not found - will use first label or index 0")
    
    print("\nProcessing dataset...")
    
    # Process each split
    processed_splits = {}
    for split_name in dataset.keys():
        print(f"\nProcessing {split_name} split ({len(dataset[split_name])} examples)...")
        
        # Step 1: Convert multi-label to single label
        print("  Converting labels...")
        split_dataset = dataset[split_name].map(
            lambda x: convert_labels_to_single(x, label_names),
            remove_columns=['labels']  # Remove old labels column
        )
        
        # Step 2: Tokenize text
        print("  Tokenizing text...")
        split_dataset = split_dataset.map(
            lambda x: tokenize_text(x, tokenizer),
            batched=True,
            remove_columns=['text']  # Remove original text column
        )
        
        processed_splits[split_name] = split_dataset
        
        # Show example
        print(f"  Example processed sample:")
        example = split_dataset[0]
        for key in example.keys():
            if key == 'input_ids':
                print(f"    {key}: {example[key][:10]}... (length: {len(example[key])})")
            elif key == 'attention_mask':
                print(f"    {key}: {example[key][:10]}... (length: {len(example[key])})")
            else:
                print(f"    {key}: {example[key]}")
    
    # Create output directory
    output_dir = "./data/go_emotions_processed"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\nSaving processed dataset to {output_dir}...")
    
    # Save the processed dataset
    from datasets import DatasetDict
    processed_dataset = DatasetDict(processed_splits)
    processed_dataset.save_to_disk(output_dir)
    
    print(f"\n✓ Dataset saved successfully to {output_dir}")
    print(f"\nDataset structure:")
    print(f"  Splits: {list(processed_dataset.keys())}")
    print(f"  Features: {list(processed_dataset['train'].features.keys())}")
    print(f"  Train size: {len(processed_dataset['train'])}")
    if 'validation' in processed_dataset:
        print(f"  Validation size: {len(processed_dataset['validation'])}")
    if 'test' in processed_dataset:
        print(f"  Test size: {len(processed_dataset['test'])}")

if __name__ == "__main__":
    main()

