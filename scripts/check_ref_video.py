import urllib.request
import re

url = 'https://www.youtube.com/watch?v=EFmxPMdBqmU'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        title_match = re.search(r'<title>(.*?)</title>', html)
        print('Video Title:', title_match.group(1) if title_match else 'Not found')
        desc_match = re.search(r'"shortDescription":"(.*?)"', html)
        if desc_match:
            print('Video Description:', desc_match.group(1)[:400])
except Exception as e:
    print('Error:', e)

