import json

path = r'D:\Projects\FindMyCampus\findmycampus\data\campus_maps.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for m in data.get('maps', []):
    if m.get('id') == '500':
        m['source_svg'] = 'Chennai, Tamil Nadu-1.svg'
    elif m.get('id') == '600':
        m['source_svg'] = 'Chennai, Tamil Nadu-2.svg'

with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f)
