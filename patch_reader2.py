import re

def update_html():
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Restore global sidebar
    # We remove #tab-syllabus and replace it with global-sidebar
    syllabus_tab_regex = re.compile(r'<!-- TAB: SYLLABUS -->\s*<div class="tab-panel" id="tab-syllabus">\s*<div style="padding: 20px;">\s*<h2 style="color:var\(--primary\); font-weight:800; margin-bottom:20px;">📖 المقررات</h2>\s*<div id="subjects-list" class="subjects-accordion">\s*<!-- Subjects and lessons injected here -->\s*</div>\s*</div>\s*</div>')
    
    global_sidebar_html = """
    <!-- Global Navigation Sidebar -->
    <nav class="global-sidebar" id="global-sidebar">
        <div class="sidebar-header">
            <h2>مقررات الأكاديمية</h2>
            <button class="close-sidebar" id="close-global-sidebar">✕</button>
        </div>
        <div id="subjects-list" class="subjects-accordion">
            <!-- Subjects and lessons injected here -->
        </div>
    </nav>
    <div class="sidebar-overlay" id="global-overlay"></div>
"""
    if syllabus_tab_regex.search(html):
        html = syllabus_tab_regex.sub(global_sidebar_html, html)
    else:
        print("Could not find tab-syllabus")

    # 2. Update search tab to be rich
    search_tab_regex = re.compile(r'<!-- TAB: SEARCH -->[\s\S]*?<!-- TAB: SYLLABUS -->')
    # Wait, the syllabus tab was replaced by global sidebar, so it's <!-- Global Navigation Sidebar --> now!
    
    # 3. Fix Bottom Nav (remove display:none from reader tab)
    html = html.replace('<button class="nav-btn" id="btn-nav-reader" onclick="switchTab(\'reader\', this)" style="display:none;">',
                        '<button class="nav-btn" id="btn-nav-reader" onclick="switchTab(\'reader\', this)">')

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Updated reader.html")

def update_js():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # Update switchTab logic to open sidebar if name == 'syllabus'
    switch_tab_old = """function switchTab(name, btn) {
    document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
    document.querySelectorAll('.bottom-nav .nav-btn').forEach(b=>b.classList.remove('active'));
    
    const panel = document.getElementById('tab-'+name);
    if(panel) panel.classList.add('active');"""

    switch_tab_new = """function switchTab(name, btn) {
    if (name === 'syllabus') {
        document.getElementById('global-sidebar').classList.add('open');
        document.getElementById('global-overlay').classList.add('show');
        return; // Don't switch active tab
    }
    
    document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
    document.querySelectorAll('.bottom-nav .nav-btn').forEach(b=>b.classList.remove('active'));
    
    const panel = document.getElementById('tab-'+name);
    if(panel) panel.classList.add('active');"""
    
    js = js.replace(switch_tab_old, switch_tab_new)

    # Add global-sidebar open/close logic inside DOMContentLoaded or initUIControls
    # We will add it to the top of switchTab or inside initUIControls. Let's just patch initUIControls.
    init_ui_old = """function initUIControls() {
    // Sommaire Bottom Sheet"""
    
    init_ui_new = """function initUIControls() {
    // Global Sidebar
    const globalSidebar = document.getElementById('global-sidebar');
    const globalOverlay = document.getElementById('global-overlay');
    if (globalSidebar && globalOverlay) {
        const closeGlobal = () => {
            globalSidebar.classList.remove('open');
            globalOverlay.classList.remove('show');
        };
        document.getElementById('close-global-sidebar').addEventListener('click', closeGlobal);
        globalOverlay.addEventListener('click', closeGlobal);
    }

    // Sommaire Bottom Sheet"""
    js = js.replace(init_ui_old, init_ui_new)

    # Add empty state to reader tab if currentLessonData is null
    # This is handled dynamically or we can just inject an empty state.
    # We will add an empty state to reader-content if no lesson is opened
    open_lesson_old = """function openLesson(lesson) {
    currentLessonData = lesson;"""
    open_lesson_new = """function openLesson(lesson) {
    document.getElementById('reader-content').style.display = 'block';
    currentLessonData = lesson;"""
    js = js.replace(open_lesson_old, open_lesson_new)

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)
    print("Updated reader.js")

if __name__ == '__main__':
    update_html()
    update_js()
