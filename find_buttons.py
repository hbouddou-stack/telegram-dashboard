import io, re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with io.open('buttons_context.txt', 'w', encoding='utf-8') as out:
    for i, l in enumerate(lines):
        if any(x in l.lower() for x in ['whatsapp', 'unlink', 'profile-unlink', 'btn-action', 'modal-actions', 'send_whatsapp', 'send_email', 'envoyer']):
            out.write(f"{i+1}: {l}")

print("Done - saved to buttons_context.txt")
