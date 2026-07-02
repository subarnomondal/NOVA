import os
import re

# Add timeout=10 to requests.get/post calls missing a timeout
files_needing_timeout = ['skills/whatsapp_call.py']

for fpath in files_needing_timeout:
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    original = content
    # Add timeout=10 to requests.get( or requests.post( that don't already have timeout
    lines = content.splitlines(keepends=True)
    new_lines = []
    for line in lines:
        if ('requests.get(' in line or 'requests.post(' in line) and 'timeout' not in line:
            # Add timeout=10 before the closing paren of the call
            line = re.sub(r'(requests\.(get|post)\([^)]+?)(\))', r'\1, timeout=10\3', line)
        new_lines.append(line)
    content = ''.join(new_lines)
    if content != original:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Fixed timeouts: {fpath}')
    else:
        print(f'No change: {fpath}')

print('Done.')
