import json
p='scripts/validation_output/github_run_26711895310_jobs.json'
raw=open(p,'rb').read()
enc='utf-8'
if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
    enc='utf-16'
else:
    try:
        raw.decode('utf-8')
    except:
        enc='latin1'
s=raw.decode(enc)
obj=json.loads(s)
print('total_jobs=', obj.get('total_count'))
jobs = obj.get('jobs', [])
summary=[]
for j in jobs:
    summary.append({'id':j.get('id'), 'name': j.get('name'), 'status': j.get('status'), 'conclusion': j.get('conclusion'), 'steps': [{'name':st.get('name'), 'conclusion': st.get('conclusion')} for st in j.get('steps',[])]})
open('scripts/validation_output/github_run_26711895310_jobs_summary.json','w',encoding='utf-8').write(json.dumps(summary, indent=2))
print('WROTE summary')
