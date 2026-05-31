import json
p='scripts/validation_output/github_run_26711895310_details.json'
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
print('name:', obj.get('name'))
print('status:', obj.get('status'), 'conclusion:', obj.get('conclusion'))
print('logs_url:', obj.get('logs_url'))
open('scripts/validation_output/github_run_26711895310_run_summary.json','w',encoding='utf-8').write(json.dumps({'name':obj.get('name'),'status':obj.get('status'),'conclusion':obj.get('conclusion'),'logs_url':obj.get('logs_url')}, indent=2))
print('WROTE')
