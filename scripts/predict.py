"""
CLI entry point for emotion prediction.

Implementation lives in `model.predict` (alongside saved weights in `model/`).
Run from project root:  python scripts/predict.py
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from model.predict import load_model, predict_emotion

if __name__ == "__main__":
    print("=" * 60)
    print("Emotion Prediction Script")
    print("=" * 60)

    load_model()

    test_texts = [
        "my roommates dont turn off the light at night and it bothers me a lot.",
        "im unable to make a girlfriend",
        "I feel anxious about the exam.",
        "What a beautiful day!",
    ]

    print("\nTesting predictions:")
    print("-" * 60)
    for text in test_texts:
        label_id, label_name, probability = predict_emotion(text)
        print(f"Text: '{text}'")
        print(f"  Predicted Label ID: {label_id}")
        print(f"  Predicted Label: {label_name}")
        print(f"  Probability: {probability:.4f}")
        print()
