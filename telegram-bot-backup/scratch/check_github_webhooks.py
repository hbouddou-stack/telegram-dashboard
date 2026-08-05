import urllib.request
import json

token = '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'
repos = ['telegram-dashboard', 'bot_quizz_albaji', 'bot-secours-academy']
for r in repos:
    url = f'https://api.github.com/repos/hbouddou-stack/{r}/hooks'
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'token {token}')
    req.add_header('User-Agent', 'Mozilla/5.0')
    try:
        with urllib.request.urlopen(req) as resp:
            hooks = json.loads(resp.read().decode())
            print(f"=== Repo: {r} ===")
            for h in hooks:
                config = h.get('config', {})
                print(f"Hook URL: {config.get('url')}")
    except Exception as e:
        print(f"{r} -> Error: {e}")
