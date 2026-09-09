import io

with io.open('dashboard/ask.html', 'r', encoding='utf-8') as f:
    text = f.read()

old_vars = """            const tid = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user ? window.Telegram.WebApp.initDataUnsafe.user.id : null) || null;
            const username = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user ? window.Telegram.WebApp.initDataUnsafe.user.username : "") || "";
            const first_name = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user ? window.Telegram.WebApp.initDataUnsafe.user.first_name : "") || "";"""

new_vars = """            const urlParams = new URLSearchParams(window.location.search);
            let tid = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user ? window.Telegram.WebApp.initDataUnsafe.user.id : null);
            if (!tid) tid = urlParams.get('telegram_id') || urlParams.get('tid') || null;
            
            let username = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user ? window.Telegram.WebApp.initDataUnsafe.user.username : "");
            if (!username) username = urlParams.get('username') || "";
            
            let first_name = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user ? window.Telegram.WebApp.initDataUnsafe.user.first_name : "");
            if (!first_name) first_name = urlParams.get('first_name') || "الطالب";"""

text = text.replace(old_vars, new_vars)

# Also let's fix the submitTicket to reload the inbox automatically or load tickets
# Currently it just shows success-screen.
# Wait, let's look at the success screen logic.

with io.open('dashboard/ask.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Vars patched.")
