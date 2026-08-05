import re

content = open('web/index_backup_restored.html', 'r', encoding='utf-16').read()

s_start = content.find('<div id="settings-modal"')
s_end = content.find('<!-- END SETTINGS MODAL -->', s_start)
if s_start != -1 and s_end != -1:
    open('web/settings_modal.html', 'w', encoding='utf-8').write(content[s_start:s_end])
else:
    print('Failed settings')

l_start = content.find('<div id="logs-modal"')
l_end = content.find('</main>', l_start) + 7
l_end = content.find('</div>', l_end) + 6 # close main wrap
l_end = content.find('</div>', l_end) + 6 # close logs-modal

if l_start != -1:
    open('web/logs_modal.html', 'w', encoding='utf-8').write(content[l_start:l_end])
else:
    print('Failed logs')

print("Extraction complete!")
