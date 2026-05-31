import json, os
from pathlib import Path

IN = Path('scripts/validation_output/chat_results.json')
MEM = Path('scripts/validation_output/memory.json')
OUT = Path('scripts/validation_output/results_with_timestamps.html')

data = json.loads(IN.read_text(encoding='utf-8'))
mem = json.loads(MEM.read_text(encoding='utf-8')) if MEM.exists() else {}

# Build video durations map from metadata in memory sources if available
video_durations = {}
# try to read durations from /metadata endpoint via earlier saved metadata? fallback none
for src in mem.get('sources', []):
    md = src.get('metadata', {})
    vid = md.get('video_id')
    # duration may not be present
    if vid and md.get('duration_seconds'):
        video_durations[vid] = float(md.get('duration_seconds'))

# Fallback: assign default duration 60s
DEFAULT_DURATION = 60.0

# Helper to assign synthetic timestamps
for vid in data.get('video_ids', []):
    # count chunks for this video across all results
    pass

# Create mapping video_id -> max chunk_id
max_chunks = {}
for res in data['results']:
    for c in res.get('chunks', []):
        for cit in c.get('citations', []):
            vid = cit.get('video_id')
            cid = cit.get('chunk_id') or 1
            max_chunks.setdefault(vid, set()).add(cid)

max_chunk_count = {vid: max(s) if s else 1 for vid, s in max_chunks.items()}

# assign timestamps per chunk
for res in data['results']:
    for c in res.get('chunks', []):
        for cit in c.get('citations', []):
            vid = cit.get('video_id')
            total = max_chunk_count.get(vid, 1)
            duration = video_durations.get(vid, DEFAULT_DURATION)
            per = duration / max(total,1)
            cid = cit.get('chunk_id') or 1
            start = round((cid-1)*per, 2)
            end = round(cid*per, 2)
            cit['timestamp_start'] = start
            cit['timestamp_end'] = end
    # also update final citations if present
    final_cits = res.get('final', {}).get('citations') if isinstance(res.get('final'), dict) else None
    if final_cits:
        for cit in final_cits:
            vid = cit.get('video_id')
            total = max_chunk_count.get(vid, 1)
            duration = video_durations.get(vid, DEFAULT_DURATION)
            per = duration / max(total,1)
            cid = cit.get('chunk_id') or 1
            start = round((cid-1)*per, 2)
            end = round(cid*per, 2)
            cit['timestamp_start'] = start
            cit['timestamp_end'] = end

# regenerate HTML
html = ['<html><body style="font-family:Arial,sans-serif;padding:20px">', '<h1>Validation Chat Results (with synthetic timestamps)</h1>']
for res in data['results']:
    html.append(f"<h2>Q: {res.get('question')}</h2>")
    final = res.get('final', {})
    answer = final.get('answer') if isinstance(final, dict) else ''
    citations = final.get('citations') if isinstance(final, dict) else None
    html.append(f"<div style='border:1px solid #ccc;padding:10px;margin-bottom:10px'><strong>Answer:</strong><div>{answer}</div>")
    html.append('<div><strong>Citations:</strong></div>')
    if citations:
        html.append('<ul>')
        for c in citations:
            ts = f"{c.get('timestamp_start')} - {c.get('timestamp_end')}"
            html.append(f"<li>{c.get('title')} ({c.get('video_id')}) - {ts} - <a href='{c.get('url')}'>{c.get('url')}</a></li>")
        html.append('</ul>')
    html.append('</div>')

html.append('<h2>Memory</h2>')
html.append(f"<pre>{json.dumps(mem, indent=2)}</pre>")
html.append('</body></html>')
OUT.write_text('\n'.join(html), encoding='utf-8')
print('Wrote', OUT)
