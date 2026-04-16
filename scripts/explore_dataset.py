"""
Script to explore the go_emotions dataset from HuggingFace.
This script loads the dataset, displays its splits, an example, and label names.
"""

from datasets import load_dataset
import os

def main():
    print("Loading go_emotions dataset from HuggingFace...")
    
    # Get the default cache directory
    cache_dir = os.path.expanduser("~/.cache/huggingface/datasets")
    print(f"\nDataset cache location: {cache_dir}")
    
    # Load the simplified version of go_emotions dataset
    dataset = load_dataset("go_emotions", "simplified")
    
    # Find the actual dataset directory
    dataset_name = "go_emotions"
    config_name = "simplified"
    dataset_path = os.path.join(cache_dir, dataset_name, config_name)
    
    if os.path.exists(dataset_path):
        print(f"go_emotions dataset path: {dataset_path}")
        # List files in the dataset directory
        if os.path.isdir(dataset_path):
            files = os.listdir(dataset_path)
            if files:
                print(f"  Contains {len(files)} files/directories")
    else:
        # Try alternative path structure
        alt_path = os.path.join(cache_dir, f"{dataset_name}---{config_name}")
        if os.path.exists(alt_path):
            print(f"go_emotions dataset path: {alt_path}")
        else:
            print(f"  Note: Check subdirectories in: {cache_dir}")
    
    print("\n" + "="*60)
    print("Dataset Splits:")
    print("="*60)
    for split_name in dataset.keys():
        print(f"  - {split_name}: {len(dataset[split_name])} examples")
    
    print("\n" + "="*60)
    print("Example from 'train' split:")
    print("="*60)
    example = dataset['train'][0]
    for key, value in example.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*60)
    print("Label Names:")
    print("="*60)
    # Get label names from the dataset features
    label_names = dataset['train'].features['labels'].feature.names
    for i, name in enumerate(label_names):
        print(f"  {i}: {name}")
    
    print(f"\nTotal number of labels: {len(label_names)}")

if __name__ == "__main__":
    main()

