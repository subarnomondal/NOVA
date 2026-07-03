import os
import re

remaining_files = [
    'skills/calendar_skill.py',
    'skills/downloader.py',
    'skills/email_service.py',
    'skills/messenger.py',
    'skills/science_skill.py',
    'skills/whatsapp_call.py',
    'skills/windows_cmd.py',
    'skills/system.py',
]

def add_encoding(content):
    """Add encoding='utf-8' to open() calls that don't have it and aren't binary mode."""
    pattern = re.compile(r"open\(([^)]+?),\s*'([rwa])'\s*\)")
    def replacer(m):
        args = m.group(1)
        mode = m.group(2)
        return f"open({args}, '{mode}', encoding='utf-8')"
    return pattern.sub(replacer, content)

for fpath in remaining_files:
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    original = content

    # Add encoding to open() calls
    content = add_encoding(content)

    # Fix bare excepts
    content = content.replace('        except: pass\n', '        except Exception:\n            pass\n')
    content = content.replace('    except: pass\n', '    except Exception:\n        pass\n')

    if content != original:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Fixed: {fpath}')
    else:
        print(f'No change: {fpath}')

print('Done.')
