import json
import os

try:
    with open(r'C:\Users\SUNDARESH MONDAL\.gemini\antigravity-ide\brain\ddf1caa6-13a0-48af-9a12-27594ecb6e3a\.system_generated\steps\344\output.txt', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for i, comp in enumerate(data.get('outputComponents', [])):
        if 'design' in comp:
            print(f'design keys: {list(comp["design"].keys())}')
            # Let's see if there is screen or html inside design
            if 'screen' in comp['design']:
                print(f'  nested screen keys: {list(comp["design"]["screen"].keys())}')
                if 'htmlCode' in comp["design"]["screen"]:
                    print('    HAS htmlCode:', comp["design"]["screen"]["htmlCode"])
            # Dump the whole design object keys if it's small enough, or just first level
            for k, v in comp['design'].items():
                if isinstance(v, dict):
                    print(f'  {k} keys: {list(v.keys())}')
                else:
                    print(f'  {k}: (type {type(v).__name__})')
except Exception as e:
    print('Error:', e)
