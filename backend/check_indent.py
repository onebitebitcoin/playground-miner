
import re

with open('backend/blocks/views.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if i >= 3240 and i < 3260:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        print(f"Line {i+1}: {indent} spaces | {stripped[:20]}...")
