"""Test redesigned preprocessing pipeline."""

import sys
from pathlib import Path

# Add app to path
app_path = Path(__file__).parent / "app"
sys.path.insert(0, str(app_path))

from preprocessing.pipeline import PreprocessingPipeline

# Test 1: Header/Footer detection with complete line removal
print("=" * 70)
print("TEST 1: Header/Footer Removal (Complete Lines)")
print("=" * 70)

test1 = """Machine Learning (BCS602)

Machine Learning is a branch of AI.

Machine Learning (BCS602)

Machine Learning is used in healthcare.

Machine Learning (BCS602)"""

pipeline = PreprocessingPipeline()
result1 = pipeline.execute(test1)

print("INPUT:")
print(test1)
print("\nOUTPUT:")
print(result1)
print()

# Test 2: Orphan word handling
print("=" * 70)
print("TEST 2: Orphan Word Merging")
print("=" * 70)

test2 = """Data analytics is a field.
analytics

is used everywhere.

Another standalone
word

should be merged."""

result2 = pipeline.execute(test2)

print("INPUT:")
print(test2)
print("\nOUTPUT:")
print(result2)
print()

# Test 3: Preserve legitimate repeated content
print("=" * 70)
print("TEST 3: Preserve Legitimate Repeated Content")
print("=" * 70)

test3 = """Machine learning is important.

The importance of machine learning.

Machine learning is important.

More text about machine learning.

Machine learning is important."""

result3 = pipeline.execute(test3)

print("INPUT:")
print(test3)
print("\nOUTPUT:")
print(result3)
print()
