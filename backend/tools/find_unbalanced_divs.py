import re
import sys

def analyze(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    # Find tags with line numbers
    pattern = re.compile(r"(</?div\b[^>]*>)", re.IGNORECASE)
    stack = []
    unmatched_closes = []
    for m in pattern.finditer(text):
        tag = m.group(1)
        start = m.start(1)
        line = text.count('\n', 0, start) + 1
        if tag.lower().startswith('</'):
            if stack:
                stack.pop()
            else:
                unmatched_closes.append((line, tag))
        else:
            stack.append((line, tag))
    return stack, unmatched_closes

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: find_unbalanced_divs.py <file>')
        sys.exit(1)
    path = sys.argv[1]
    opens, closes = analyze(path)
    if not opens and not closes:
        print('No unbalanced <div> tags detected in', path)
    else:
        if closes:
            print('Unmatched closing </div> at lines:')
            for ln, tag in closes:
                print(f'  line {ln}: {tag}')
        if opens:
            print('Unclosed opening <div> at lines:')
            for ln, tag in opens:
                print(f'  line {ln}: {tag}')
