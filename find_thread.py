import io
import re

with io.open('dashboard/ask.html', 'r', encoding='utf-8') as f:
    text = f.read()

def safe_print(s):
    print(s.encode('ascii', 'backslashreplace').decode('ascii'))

print("--- CSS for ticket threads ---")
for match in re.finditer(r'\.ticket-.*?\{[^}]*\}', text):
    safe_print(match.group(0))

print("\n--- HTML for ticket threads ---")
thread_div = re.search(r'<div[^>]*id="ticket-thread-view"[^>]*>.*?</div>\s*</div>\s*</div>', text, re.DOTALL)
if thread_div:
    safe_print(thread_div.group(0)[:800])

print("\n--- Render Function for threads ---")
render_func = re.search(r'function openTicketThread.*?}', text, re.DOTALL)
if render_func:
    safe_print(render_func.group(0)[:800])
