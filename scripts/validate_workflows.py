import yaml
import re
import json

files = [
    '.github/workflows/backend-ci.yml',
    '.github/workflows/frontend-ci.yml',
    '.github/workflows/smoke-test.yml',
    '.github/workflows/deployment.yml',
]

results = {}
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            txt = fh.read()
        yaml.safe_load(txt)
        secrets = sorted(list(set(re.findall(r"\$\{\{\s*secrets\.([A-Za-z0-9_]+)\s*\}\}", txt))))
        results[f] = {"valid": True, "secrets": secrets}
    except Exception as e:
        results[f] = {"valid": False, "error": str(e)}

print(json.dumps(results, indent=2))
