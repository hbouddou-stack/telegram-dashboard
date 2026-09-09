import io
import re

try:
    with io.open('dashboard/ask.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    print(f"Total size: {len(html)} chars")
    
    # Let's extract ticket creation logic
    ticket_creation = re.search(r'function submitTicket.*?}', html, re.DOTALL)
    if ticket_creation:
        print("\n--- Ticket Creation JS ---")
        print(ticket_creation.group(0)[:500])
        
    # Let's extract the ticket fetching logic
    ticket_fetch = re.search(r'function fetchMyTickets.*?}', html, re.DOTALL)
    if ticket_fetch:
        print("\n--- Ticket Fetch JS ---")
        print(ticket_fetch.group(0)[:500])
        
    # Check layout (sidebar)
    sidebar = re.search(r'<div[^>]*class="[^"]*sidebar[^"]*"[^>]*>', html)
    if sidebar:
        print("\n--- Sidebar HTML ---")
        print(sidebar.group(0))
        
    # Check FAQ structure
    faq = re.search(r'function renderFAQ.*?}', html, re.DOTALL)
    if faq:
        print("\n--- FAQ JS ---")
        print(faq.group(0)[:500])

except Exception as e:
    print("Error:", e)
