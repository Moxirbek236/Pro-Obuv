#!/usr/bin/env python3
"""Test if base.html has Jinja2 syntax errors"""
import sys
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError

try:
    env = Environment(loader=FileSystemLoader('templates'))
    print("Testing base.html template syntax...")
    template = env.get_template('base.html')
    print("✓ base.html loaded successfully - no Jinja2 syntax errors!")
except TemplateSyntaxError as e:
    print(f"✗ Jinja2 syntax error in base.html:")
    print(f"  Line {e.lineno}: {e.message}")
    print(f"  {e.source}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error loading template: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
