"""Test preprocessing pipeline."""

import sys
from pathlib import Path

# Add app to path
app_path = Path(__file__).parent / "app"
sys.path.insert(0, str(app_path))

from preprocessing.pipeline import PreprocessingPipeline

# Sample text with issues that should be cleaned
sample = """Machine Learning (BCS602)

17

vtucircle.com

Machine learning is an important
branch of AI.

MODULE - 1

More content about machine learning.
The field is rapidly evolving."""

pipeline = PreprocessingPipeline()
cleaned = pipeline.execute(sample)

print("ORIGINAL:")
print("=" * 60)
print(sample)
print()
print("CLEANED OUTPUT:")
print("=" * 60)
print(cleaned)
print("=" * 60)
