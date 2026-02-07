#!/usr/bin/env python3
"""Test if templates parse correctly without Jinja errors."""

from jinja2 import Environment, FileSystemLoader
import sys

def test_template(name):
    """Test if a template can be parsed."""
    try:
        env = Environment(loader=FileSystemLoader('templates'))
        # Add a dummy cloudinary_url filter to avoid filter errors
        env.filters['cloudinary_url'] = lambda x: x
        tmpl = env.get_template(name)
        return True, None
    except Exception as e:
        return False, str(e)

templates = ['base.html', 'menu.html', 'news.html']
all_good = True

for tpl in templates:
    success, error = test_template(tpl)
    status = "✓ OK" if success else "✗ ERROR"
    print(f"{status}: {tpl}")
    if error:
        # Show just the first line of the error
        error_lines = error.split('\n')
        for line in error_lines:
            if 'Error' in line or 'error' in line:
                print(f"  {line.strip()}")
                break
        all_good = False

sys.exit(0 if all_good else 1)
