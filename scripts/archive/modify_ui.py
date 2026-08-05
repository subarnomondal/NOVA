import re

def inject_html():
    try:
        content = open('web/index.html', 'r', encoding='utf-8').read()
        
        # 1. Avatar Dropdown (Without Logout)
        avatar_search = re.search(r'<div class="relative group">\s*<div class="w-8 h-8 rounded-full border-2 border-primary overflow-hidden\s*shadow-\[0_0_10px_rgba\(221,183,255,0\.5\)\]">', content)
        if avatar_search:
            avatar_html = '''<div class="relative group" id="avatar-container">
<div id="avatar-btn" class="w-8 h-8 rounded-full border-2 border-primary overflow-hidden shadow-[0_0_10px_rgba(221,183,255,0.5)] cursor-pointer hover:scale-105 transition-transform">'''
            content = content[:avatar_search.start()] + avatar_html + content[avatar_search.end():]
        else:
            print("Could not find avatar start!")

        dropdown = '''
<div id="avatar-dropdown" class="absolute right-0 mt-2 w-48 rounded-xl glass-panel shadow-2xl border border-white/10 hidden flex-col overflow-hidden" style="z-index: 100;">
    <div class="p-3 hover:bg-white/5 cursor-pointer text-on-surface text-sm transition-colors">👤 Profile</div>
    <div class="p-3 hover:bg-white/5 cursor-pointer text-on-surface text-sm transition-colors">⚙️ Preferences</div>
</div>
</div>
'''
        header_end = content.find('</header>')
        if header_end != -1:
            div_ends = content.rfind('</div>\n</div>\n</div>', 0, header_end)
            if div_ends != -1:
                content = content[:div_ends] + '</div>\n' + dropdown + '\n</div>' + content[div_ends + 20:]
            else:
                print("Could not find closing divs for avatar!")

        # 2. Add IDs to Sidebar Links using exact strings
        content = content.replace('<span class="font-label-mono text-label-mono uppercase tracking-widest">Chat</span>', '<span class="font-label-mono text-label-mono uppercase tracking-widest" id="sidebar-chat-btn">Chat</span>')
        content = content.replace('<span class="font-label-mono text-label-mono uppercase tracking-widest">History</span>', '<span class="font-label-mono text-label-mono uppercase tracking-widest" id="sidebar-history-btn">History</span>')
        content = content.replace('<span class="font-label-mono text-label-mono uppercase tracking-widest">Live Mode</span>', '<span class="font-label-mono text-label-mono uppercase tracking-widest" id="sidebar-live-btn">Live Mode</span>')
        content = content.replace('<span class="font-label-mono text-label-mono uppercase tracking-widest">Tools</span>', '<span class="font-label-mono text-label-mono uppercase tracking-widest" id="sidebar-tools-btn">Tools</span>')
        content = content.replace('<span class="font-label-mono text-label-mono uppercase tracking-widest">Settings</span>', '<span class="font-label-mono text-label-mono uppercase tracking-widest" id="sidebar-settings-btn">Settings</span>')
        
        # 3. Remove Logout button from Sidebar entirely
        # It's an anchor tag. Let's use regex to find and remove the whole <a>...</a> block that contains "Logout"
        logout_regex = r'<a class="flex items-center gap-4 px-4 py-3 rounded-lg text-error hover:bg-error/10 transition-colors mt-auto" href="#">\s*<span class="material-symbols-outlined">logout</span>\s*<span class="font-label-mono text-label-mono uppercase">Logout</span>\s*</a>'
        content = re.sub(logout_regex, '', content, flags=re.MULTILINE)
        
        # 4. Modals Injection
        modals_html = """
<!-- INJECTED MODALS -->
<div id="logs-modal" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-md hidden">
    <div class="glass-panel w-full max-w-4xl h-[80vh] rounded-[24px] flex flex-col overflow-hidden shadow-2xl relative border border-white/10 bg-surface/80 p-6">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-headline-sm font-bold text-primary">Chat History</h2>
            <button id="close-logs-modal-btn" class="material-symbols-outlined text-on-surface hover:text-error transition-colors">close</button>
        </div>
        <div class="flex-1 overflow-y-auto pr-2" id="logs-content">
            <p class="text-on-surface-variant opacity-70">Loading history logs...</p>
        </div>
    </div>
</div>

<div id="settings-modal" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-md hidden">
    <div class="glass-panel w-full max-w-2xl rounded-[24px] flex flex-col overflow-hidden shadow-2xl relative border border-white/10 bg-surface/80 p-6">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-headline-sm font-bold text-primary">System Settings</h2>
            <button id="close-settings-modal-btn" class="material-symbols-outlined text-on-surface hover:text-error transition-colors">close</button>
        </div>
        <div class="flex-1 flex flex-col gap-4">
            <div>
                <label class="block text-sm font-medium text-on-surface-variant mb-1">Theme</label>
                <select class="w-full bg-surface-container rounded-lg p-2 border border-white/5 text-on-surface">
                    <option>Dark Mode</option>
                    <option>Light Mode</option>
                    <option>System Default</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-medium text-on-surface-variant mb-1">Notifications</label>
                <label class="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" checked class="rounded border-white/20 bg-surface-container text-primary focus:ring-primary focus:ring-offset-surface">
                    <span class="text-on-surface text-sm">Enable sound alerts</span>
                </label>
            </div>
            <button class="mt-4 bg-primary text-on-primary font-medium py-2 rounded-lg hover:bg-primary/90 transition-colors">Save Changes</button>
        </div>
    </div>
</div>

<div id="live-overlay" class="fixed inset-0 z-[90] flex items-center justify-center bg-black/95 hidden flex-col">
    <div class="w-32 h-32 rounded-full border-4 border-primary/30 animate-[ping_2s_cubic-bezier(0,0,0.2,1)_infinite] absolute"></div>
    <div class="w-24 h-24 rounded-full border-4 border-primary/60 animate-pulse absolute"></div>
    <div class="material-symbols-outlined text-6xl text-primary z-10 animate-bounce">mic</div>
    <p class="text-primary mt-8 font-headline-sm tracking-widest z-10 uppercase animate-pulse">Live Mode Active</p>
    <button id="close-live-btn" class="mt-12 px-6 py-2 rounded-full border border-error text-error hover:bg-error hover:text-on-error transition-colors z-10">End Session</button>
</div>
<!-- END INJECTED MODALS -->
"""
        content = content.replace('</body>', modals_html + '\n</body>')

        # 5. Right Sidebar IDs
        # "Web Browser", "Code Interpreter", "Data Analysis"
        content = content.replace('<p class="text-sm font-medium text-on-surface">Web Browser</p>', '<p class="text-sm font-medium text-on-surface" id="tool-web-browser">Web Browser</p>')
        content = content.replace('<p class="text-sm font-medium text-on-surface">Code Interpreter</p>', '<p class="text-sm font-medium text-on-surface" id="tool-code-interpreter">Code Interpreter</p>')
        content = content.replace('<p class="text-sm font-medium text-on-surface">Data Analysis</p>', '<p class="text-sm font-medium text-on-surface" id="tool-data-analysis">Data Analysis</p>')
        
        # 6. Inject Logic Script
        script_html = """
<script>
    document.addEventListener('DOMContentLoaded', () => {
        // Avatar Logic
        const avatarContainer = document.getElementById('avatar-container');
        const avatarBtn = document.getElementById('avatar-btn');
        const avatarDropdown = document.getElementById('avatar-dropdown');
        
        if (avatarBtn && avatarDropdown) {
            avatarBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                avatarDropdown.classList.toggle('hidden');
                avatarDropdown.classList.toggle('flex');
            });
            
            document.addEventListener('click', (e) => {
                if (!avatarContainer.contains(e.target)) {
                    avatarDropdown.classList.add('hidden');
                    avatarDropdown.classList.remove('flex');
                }
            });
        }
        
        // Sidebar Links Logic
        const sidebarChatBtn = document.getElementById('sidebar-chat-btn');
        const sidebarHistoryBtn = document.getElementById('sidebar-history-btn');
        const sidebarLiveBtn = document.getElementById('sidebar-live-btn');
        const sidebarToolsBtn = document.getElementById('sidebar-tools-btn');
        const sidebarSettingsBtn = document.getElementById('sidebar-settings-btn');
        
        const logsModal = document.getElementById('logs-modal');
        const settingsModal = document.getElementById('settings-modal');
        const liveOverlay = document.getElementById('live-overlay');
        
        const closeLogsBtn = document.getElementById('close-logs-modal-btn');
        const closeSettingsBtn = document.getElementById('close-settings-modal-btn');
        const closeLiveBtn = document.getElementById('close-live-btn');
        
        function hideAll() {
            if (logsModal) logsModal.classList.add('hidden');
            if (settingsModal) settingsModal.classList.add('hidden');
            if (liveOverlay) liveOverlay.classList.add('hidden');
        }
        
        if (sidebarChatBtn) {
            sidebarChatBtn.parentElement.parentElement.addEventListener('click', () => {
                hideAll();
            });
        }
        
        if (sidebarHistoryBtn) {
            sidebarHistoryBtn.parentElement.parentElement.addEventListener('click', () => {
                hideAll();
                if (logsModal) logsModal.classList.remove('hidden');
            });
        }
        
        if (sidebarLiveBtn) {
            sidebarLiveBtn.parentElement.parentElement.addEventListener('click', () => {
                hideAll();
                if (liveOverlay) liveOverlay.classList.remove('hidden');
            });
        }
        
        if (sidebarSettingsBtn) {
            sidebarSettingsBtn.parentElement.parentElement.addEventListener('click', () => {
                hideAll();
                if (settingsModal) settingsModal.classList.remove('hidden');
            });
        }
        
        if (sidebarToolsBtn) {
            sidebarToolsBtn.parentElement.parentElement.addEventListener('click', () => {
                // Focus on the right sidebar
                document.getElementById('tool-web-browser').scrollIntoView({behavior: 'smooth', block: 'center'});
            });
        }
        
        // Close Buttons
        if (closeLogsBtn) closeLogsBtn.addEventListener('click', hideAll);
        if (closeSettingsBtn) closeSettingsBtn.addEventListener('click', hideAll);
        if (closeLiveBtn) closeLiveBtn.addEventListener('click', hideAll);
        
        // Right Sidebar Tools Logic
        const toolWeb = document.getElementById('tool-web-browser');
        const toolCode = document.getElementById('tool-code-interpreter');
        const toolData = document.getElementById('tool-data-analysis');
        
        function addToolClick(el) {
            if (!el) return;
            // The container is two levels up
            const container = el.parentElement.parentElement;
            container.addEventListener('click', () => {
                const originalText = el.innerText;
                el.innerText = 'Initializing...';
                el.classList.add('animate-pulse');
                setTimeout(() => {
                    el.innerText = originalText + ' (Active)';
                    el.classList.remove('animate-pulse');
                    el.classList.add('text-primary');
                }, 1000);
            });
        }
        
        addToolClick(toolWeb);
        addToolClick(toolCode);
        addToolClick(toolData);
    });
</script>
"""
        content = content.replace('</body>', script_html + '\n</body>')

        open('web/index.html', 'w', encoding='utf-8').write(content)
        print('Injected cleanly!')
    except Exception as e:
        print('Error:', e)
        
inject_html()
