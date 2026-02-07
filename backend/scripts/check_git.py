#!/usr/bin/env python
import os
import struct

# Try to read git object directly
git_dir = '.git/objects'

# Find all objects and try to read them
for root, dirs, files in os.walk(git_dir):
    for file in files[:5]:  # Just check first few
        path = os.path.join(root, file)
        print(f"Found git object: {path}")
