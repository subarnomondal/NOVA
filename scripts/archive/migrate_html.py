import re

def migrate_html():
    with open('web/stitch_assets_new/index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Add chat-feed ID
    html = html.replace(
        '<div class="flex-1 overflow-y-auto px-6 space-y-6 pb-24 scrollbar-hide">',
        '<div class="flex-1 overflow-y-auto px-6 space-y-6 pb-24 scrollbar-hide" id="chat-feed">'
    )

    # 2. Add user-input ID
    html = html.replace(
        '<input class="flex-1 bg-transparent border-none focus:ring-0 text-on-surface font-body-md px-4 placeholder:text-outline/50" placeholder="Command CLIO AI..." type="text"/>',
        '<input id="user-input" class="flex-1 bg-transparent border-none focus:ring-0 text-on-surface font-body-md px-4 placeholder:text-outline/50" placeholder="Command CLIO AI..." type="text"/>'
    )

    # 3. Add send-btn ID
    html = html.replace(
        '<button class="p-3 rounded-xl bg-secondary text-on-secondary-fixed shadow-lg hover:scale-105 active:scale-95 transition-all flex items-center justify-center">\n<span class="material-symbols-outlined">send</span>\n</button>',
        '<button id="send-btn" class="p-3 rounded-xl bg-secondary text-on-secondary-fixed shadow-lg hover:scale-105 active:scale-95 transition-all flex items-center justify-center">\n<span class="material-symbols-outlined">send</span>\n</button>'
    )
    
    # 4. Replace the "add_circle" button with our upload-btn and hidden file input, plus mic buttons
    add_circle_orig = '''<button class="p-2 text-outline hover:text-primary transition-colors">
<span class="material-symbols-outlined">add_circle</span>
</button>'''
    
    new_buttons = '''<button id="upload-btn" class="p-2 text-outline hover:text-primary transition-colors">
<span class="material-symbols-outlined">add_circle</span>
</button>
<input type="file" id="file-upload" class="hidden" />
<button id="mic-btn" class="p-2 text-outline hover:text-primary transition-colors">
<span class="material-symbols-outlined">mic</span>
</button>
<button id="stop-btn" class="p-2 text-error hover:text-error/80 transition-colors hidden">
<span class="material-symbols-outlined">stop_circle</span>
</button>'''
    html = html.replace(add_circle_orig, new_buttons)

    # 5. Make sure scripts exist before </body>
    script_tags = """
<script src="/eel.js"></script>
<script src="app.js"></script>
<script src="welcome.js"></script>
"""
    if '</body>' in html:
        html = html.replace('</body>', script_tags + '</body>')

    with open('web/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    print("Migration successful.")

if __name__ == "__main__":
    migrate_html()
