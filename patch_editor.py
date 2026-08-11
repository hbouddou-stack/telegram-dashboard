import re

with open('dashboard/editor.html', 'r', encoding='utf-8') as f:
    content = f.read()

style_injection = """
    <!-- EDITOR ONLY STYLES -->
    <style>
        /* Hide all sidebar sections except content (Transcripts/Mindmap) */
        #section-inbox, 
        #section-people, 
        #section-stats, 
        #section-system {
            display: none !important;
        }

        /* Hide all tab contents except transcripts and mindmap */
        #tab-inbox,
        #tab-students,
        #tab-stats,
        #tab-settings,
        #tab-reports,
        #tab-proposals {
            display: none !important;
        }

        /* Force content section to be always open */
        #section-content .sidebar-section-content {
            display: block !important;
        }
    </style>
    <script>
        // Force the default tab to be 'transcripts' when loading
        window.EDITOR_MODE = true;
        document.addEventListener("DOMContentLoaded", () => {
            setTimeout(() => {
                if(typeof switchTab === 'function') {
                    switchTab('transcripts');
                }
            }, 500);
        });
    </script>
    <!-- END EDITOR ONLY STYLES -->
"""

if "EDITOR ONLY STYLES" not in content:
    content = content.replace("</head>", style_injection + "\n</head>")

with open('dashboard/editor.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("editor.html patched.")
