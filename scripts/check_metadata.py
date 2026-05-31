import requests

resp = requests.get('http://127.0.0.1:8001/metadata', timeout=10)
print('status', resp.status_code)
js = resp.json()
videos = js.get('videos', [])
print('videos_count', len(videos))
for i, v in enumerate(videos[:10]):
    print(i+1, v.get('id'), v.get('title'))
