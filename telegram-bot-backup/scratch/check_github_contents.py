import urllib.request
import json

url = 'https://api.github.com/repos/hbouddou-stack/telegram-dashboard/contents'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        contents = json.loads(resp.read().decode())
        for c in contents:
            print(f"{c['name']}: {c['type']}")
except Exception as e:
    print('Error:', e)
