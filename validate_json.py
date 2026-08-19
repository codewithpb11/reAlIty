import json
with open('mobile-app/app.json') as f:
    json.load(f)
print('app.json is valid JSON')
