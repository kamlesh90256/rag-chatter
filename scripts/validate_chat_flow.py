import requests
import json
import os

BASE = 'http://127.0.0.1:8001'
OUT_DIR = 'scripts/validation_output'
os.makedirs(OUT_DIR, exist_ok=True)

# get top 2 video ids
m = requests.get(f'{BASE}/metadata', timeout=10).json()
videos = m.get('videos', [])
video_ids = [v['id'] for v in videos[:2]]
print('video_ids', video_ids)

thread_id = 'validation-thread-1'
questions = [
    'Why did Video A outperform Video B?',
    'Compare the hooks in the first 5 seconds.',
    'Suggest improvements for Video B based on Video A.',
    'Who is the creator of Video B and what is their follower count?',
    'What hashtags contributed to engagement?'
]

results = []

for q in questions:
    print('\nQuestion:', q)
    # streaming request
    params = {'stream': 'true'}
    payload = {'question': q, 'thread_id': thread_id, 'video_ids': video_ids, 'stream': True}
    with requests.post(f'{BASE}/chat', json=payload, stream=True, timeout=60) as r:
        if r.status_code != 200:
            print('chat failed', r.status_code, r.text)
            results.append({'question': q, 'error': r.text})
            continue
        chunks = []
        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue
            text = line.decode() if isinstance(line, bytes) else line
            # lines like 'data: {...}'
            if text.startswith('data: '):
                data = text[len('data: '):]
                if data.strip() == '[DONE]':
                    break
                try:
                    obj = json.loads(data)
                except Exception:
                    obj = {'raw': data}
                chunks.append(obj)
                print('chunk', obj.keys())
        # last chunk should contain answer and citations
        final = chunks[-1] if chunks else {}
        results.append({'question': q, 'chunks': chunks, 'final': final})

# save results
with open(os.path.join(OUT_DIR, 'chat_results.json'), 'w', encoding='utf-8') as f:
    json.dump({'video_ids': video_ids, 'results': results}, f, ensure_ascii=False, indent=2)
print('\nSaved results to', os.path.join(OUT_DIR, 'chat_results.json'))

# fetch sources/memory for thread
mem = requests.get(f'{BASE}/sources', params={'thread_id': thread_id}, timeout=10).json()
with open(os.path.join(OUT_DIR, 'memory.json'), 'w', encoding='utf-8') as f:
    json.dump(mem, f, ensure_ascii=False, indent=2)
print('Saved memory to', os.path.join(OUT_DIR, 'memory.json'))

# generate simple HTML for screenshots
html = ['<html><body style="font-family:Arial,sans-serif;padding:20px">', '<h1>Validation Chat Results</h1>']
for res in results:
    html.append(f"<h2>Q: {res.get('question')}</h2>")
    final = res.get('final', {})
    answer = final.get('answer') if isinstance(final, dict) else ''
    citations = final.get('citations') if isinstance(final, dict) else None
    if not answer:
        # try last chunk raw
        if res.get('chunks'):
            answer = res['chunks'][-1].get('answer') if isinstance(res['chunks'][-1], dict) else ''
    html.append(f"<div style='border:1px solid #ccc;padding:10px;margin-bottom:10px'><strong>Answer:</strong><div>{answer}</div>")
    html.append('<div><strong>Citations:</strong></div>')
    if citations:
        html.append('<ul>')
        for c in citations:
            html.append(f"<li>{c.get('source','')} - {c.get('start','')} to {c.get('end','')} ({c.get('text','')[:120]})</li>")
        html.append('</ul>')
    html.append('</div>')

html.append('<h2>Memory</h2>')
html.append(f"<pre>{json.dumps(mem, indent=2)}</pre>")
html.append('</body></html>')
with open(os.path.join(OUT_DIR, 'results.html'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(html))
print('Saved HTML to', os.path.join(OUT_DIR, 'results.html'))
