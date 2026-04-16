"""
Emotion detector module that loads the fine-tuned DistilBERT model
and provides functionality to detect emotions from text.
"""

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from datasets import load_dataset
import torch
import os

# Global variables to store loaded model, tokenizer, and label names
_model = None
_tokenizer = None
_label_names = None

def _load_model(model_path="./model"):
    """
    Load the fine-tuned model and tokenizer from disk, and load label names.
    
    Args:
        model_path: Path to the directory containing the saved model and tokenizer
    
    Returns:
        tuple: (model, tokenizer, label_names)
    """
    global _model, _tokenizer, _label_names
    
    if _model is None or _tokenizer is None:
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model not found at {model_path}. "
                "Please run scripts/train.py first to train and save the model."
            )
        
        _tokenizer = AutoTokenizer.from_pretrained(model_path)
        _model = AutoModelForSequenceClassification.from_pretrained(model_path)
        _model.eval()  # Set model to evaluation mode
        
        # Move model to GPU if available
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _model.to(device)
    
    # Load label names from the go_emotions dataset
    if _label_names is None:
        dataset = load_dataset("go_emotions", "simplified")
        _label_names = dataset['train'].features['labels'].feature.names
    
    return _model, _tokenizer, _label_names

def detect_emotion(text):
    """
    Detect the emotion label for the given text.
    
    Args:
        text: Input text string to classify
    
    Returns:
        str: The emotion label name (e.g., "joy", "sadness", "anger")
    """
    # Load model if not already loaded
    model, tokenizer, label_names = _load_model()
    
    # Tokenize the input text
    inputs = tokenizer(
        text,
        truncation=True,
        padding='max_length',
        max_length=128,
        return_tensors='pt'
    )
    
    # Move inputs to the same device as the model
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    # Run inference
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
    
    # Apply softmax to get probabilities
    probabilities = torch.softmax(logits, dim=-1)
    
    # Get the predicted label ID
    predicted_id = torch.argmax(probabilities, dim=-1).item()
    
    # Get the label name
    label_name = label_names[predicted_id] if predicted_id < len(label_names) else f"LABEL_{predicted_id}"
    
    return label_name






