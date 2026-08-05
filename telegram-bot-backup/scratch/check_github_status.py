import urllib.request
import json

url = 'https://api.github.com/repos/hbouddou-stack/bot-secours-academy/commits/ae1a8dba/status'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        print(f"Commit ae1a8dba State: {data.get('state')}")
except Exception as e:
    print('Error:', e)
