import urllib.request
import json

url = 'https://api.github.com/repos/hbouddou-stack/bot-secours-academy/commits?per_page=5'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        commits = json.loads(resp.read().decode())
        for c in commits:
            sha = c['sha']
            commit = c['commit']
            print(f"SHA: {sha[:8]} | Date: {commit['committer']['date']} | Msg: {commit['message']}")
except Exception as e:
    print('Error:', e)
