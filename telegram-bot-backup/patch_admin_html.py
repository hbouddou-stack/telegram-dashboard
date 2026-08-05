import sys

file_path = r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\dashboard\admin.html'
with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

modal_html = """
    <!-- Node Questions Modal -->
    <div id="node-questions-modal" class="modal-overlay" style="display: none;">
        <div class="modal-content" style="width: 800px; max-width: 90%; max-height: 80vh; display: flex; flex-direction: column;">
            <div class="modal-header">
                <h3 id="node-questions-title">الأسئلة المصنفة في هذه العقدة</h3>
                <button class="btn-close" onclick="closeNodeQuestionsModal()">&times;</button>
            </div>
            <div id="node-questions-list" class="modal-body" style="overflow-y: auto; flex: 1; padding: 20px; display: flex; flex-direction: column; gap: 10px;">
                <!-- Questions will be loaded here -->
            </div>
        </div>
    </div>
"""

# Insert the modal just before the closing body tag or near other modals.
# Search for </section> after panels or just before <script> tags.
if "<!-- Delete Category Modal -->" in html:
    html = html.replace("<!-- Delete Category Modal -->", modal_html + "\n    <!-- Delete Category Modal -->")
else:
    # Just append before the <script src="admin.js">
    html = html.replace('<script src="admin.js', modal_html + '\n    <script src="admin.js')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html)
print('Patched admin.html with modal')
