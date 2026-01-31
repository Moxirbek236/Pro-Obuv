#!/usr/bin/env python
import os
import zlib
import struct

def read_git_object(sha):
    """Read a git object by SHA"""
    obj_path = os.path.join('.git/objects', sha[:2], sha[2:])
    if not os.path.exists(obj_path):
        return None, None
    
    with open(obj_path, 'rb') as f:
        data = zlib.decompress(f.read())
    
    null_idx = data.index(b'\x00')
    header = data[:null_idx].decode()
    content = data[null_idx + 1:]
    return header, content

def parse_tree_object(data):
    """Parse a git tree object"""
    entries = {}
    pos = 0
    
    while pos < len(data):
        # Read mode and name
        space_idx = data.index(b' ', pos)
        mode = data[pos:space_idx].decode()
        
        null_idx = data.index(b'\x00', space_idx)
        name = data[space_idx + 1:null_idx].decode()
        
        # Read SHA (20 bytes)
        sha = data[null_idx + 1:null_idx + 21].hex()
        
        entries[name] = {'mode': mode, 'sha': sha}
        pos = null_idx + 21
    
    return entries

# Read current commit
with open('.git/HEAD', 'r') as f:
    ref = f.read().strip()

ref_path = '.git/' + ref[5:]
with open(ref_path, 'r') as f:
    commit_sha = f.read().strip()

print(f'Current commit: {commit_sha}')

# Read commit object
header, commit_data = read_git_object(commit_sha)
print(f'Commit type: {header}')

# Parse commit to get tree SHA
lines = commit_data.decode().split('\n')
tree_sha = None
for line in lines:
    if line.startswith('tree '):
        tree_sha = line.split()[1]
        break

print(f'Tree SHA: {tree_sha}')

# Read tree object
header, tree_data = read_git_object(tree_sha)
tree_entries = parse_tree_object(tree_data)

# Find templates directory
if 'templates' in tree_entries:
    templates_sha = tree_entries['templates']['sha']
    print(f'Templates tree SHA: {templates_sha}')
    
    # Read templates tree
    header, templates_data = read_git_object(templates_sha)
    templates_entries = parse_tree_object(templates_data)
    
    # Find base.html
    if 'base.html' in templates_entries:
        base_html_sha = templates_entries['base.html']['sha']
        print(f'base.html SHA: {base_html_sha}')
        
        # Read base.html blob
        header, base_html_content = read_git_object(base_html_sha)
        
        # Write it back
        with open('templates/base.html', 'wb') as f:
            f.write(base_html_content)
        
        print(f'✓ Successfully restored base.html!')
        print(f'  File size: {len(base_html_content)} bytes')
    else:
        print('base.html not found in templates tree')
else:
    print('templates directory not found in tree')
