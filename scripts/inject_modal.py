with open('web/settings_modal.html', 'r', encoding='utf-8') as f:
    modal_html = f.read()

with open('web/index.html', 'r', encoding='utf-8') as f:
    index_html = f.read()

if 'id="settings-modal"' not in index_html:
    insertion_point = '<script src="app.js"></script>'
    new_index_html = index_html.replace(insertion_point, modal_html + '\n' + insertion_point)
    with open('web/index.html', 'w', encoding='utf-8') as f:
        f.write(new_index_html)
    print('Modal injected successfully.')
else:
    print('Modal already exists.')
