#!/usr/bin/env python
import os
import zlib
import struct

def read_git_object(git_dir, sha):
    """Read a git object by SHA"""
    obj_path = os.path.join(git_dir, 'objects', sha[:2], sha[2:])
    if not os.path.exists(obj_path):
        return None
    
    with open(obj_path, 'rb') as f:
        data = zlib.decompress(f.read())
    
    # Parse git object format
    null_index = data.index(b'\x00')
    header = data[:null_index]
    content = data[null_index + 1:]
    
    return content

# Try to find base.html in git index
git_dir = '.git'
index_path = os.path.join(git_dir, 'index')

# Read git HEAD to find current commit
head_path = os.path.join(git_dir, 'HEAD')
with open(head_path, 'r') as f:
    head_ref = f.read().strip()

if head_ref.startswith('ref:'):
    ref_path = os.path.join(git_dir, head_ref[5:])
    if os.path.exists(ref_path):
        with open(ref_path, 'r') as f:
            commit_sha = f.read().strip()
            print(f"Current commit: {commit_sha}")

# List all objects
objects_dir = os.path.join(git_dir, 'objects')
count = 0
for root, dirs, files in os.walk(objects_dir):
    if root.endswith('pack') or root.endswith('info'):
        continue
    for file in files:
        count += 1
        if count <= 10:
            sha_prefix = os.path.basename(root)
            sha = sha_prefix + file
            print(f"Found object: {sha}")

print(f"\nTotal objects found: {count}")
print("\nTrying to restore via git reflog or finding base.html in object database...")
