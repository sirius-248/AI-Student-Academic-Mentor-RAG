"""Debug the HeaderFooterCleaner."""

import sys
import logging
from pathlib import Path

# Add app to path
app_path = Path(__file__).parent / "app"
sys.path.insert(0, str(app_path))

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

from preprocessing.header_footer_cleaner import HeaderFooterCleaner

# Test text
test = """Machine Learning (BCS602)

Machine Learning is a branch of AI.

Machine Learning (BCS602)

Machine Learning is used in healthcare.

Machine Learning (BCS602)"""

print("Input:")
print(test)
print("\n" + "="*70 + "\n")

# Create cleaner
cleaner = HeaderFooterCleaner()

# Manually check what gets detected
lines = test.split('\n')
print(f"Total lines: {len(lines)}")
print(f"Min frequency threshold: {cleaner.min_frequency}\n")

print("Lines list:")
for i, line in enumerate(lines):
    print(f"  {i}: '{line}'")

print("\n" + "="*70)
print("\nRunning _find_headers_and_footers:")
headers_to_remove = cleaner._find_headers_and_footers(lines)
print(f"\nDetected headers/footers to remove ({len(headers_to_remove)}):")
for header in headers_to_remove:
    print(f"  '{header}'")

print("\n" + "="*70)
print("Running full clean:")
result = cleaner.clean(test)
print("\nOutput:")
print(result)

print("\n" + "="*70)
print("Verification - checking line by line:")
output_lines = result.split('\n')
for i, (orig, new) in enumerate(zip(lines, output_lines)):
    if orig != new:
        print(f"  Line {i} CHANGED: '{orig}' -> '{new}'")
    else:
        print(f"  Line {i} same: '{orig}'")

