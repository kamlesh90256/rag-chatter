import json
p='scripts/validation_output/github_actions_runs.json'
raw=open(p,'rb').read()
# detect BOM/encoding
enc='utf-8'
if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
    enc='utf-16'
else:
    try:
        raw.decode('utf-8')
    except Exception:
        enc='latin1'
s=raw.decode(enc)
obj=json.loads(s)
print('total_count=', obj.get('total_count'))
runs = obj.get('workflow_runs', [])
summary = []
for run in runs[:50]:
    summary.append({
        'id': run.get('id'),
        'name': run.get('name'),
        'workflow_id': run.get('workflow_id'),
        'event': run.get('event'),
        'status': run.get('status'),
        'conclusion': run.get('conclusion'),
        'created_at': run.get('created_at'),
        'html_url': run.get('html_url')
    })
open('scripts/validation_output/github_actions_runs_summary.json','w',encoding='utf-8').write(json.dumps(summary, indent=2))
print('WROTE summary to scripts/validation_output/github_actions_runs_summary.json')
