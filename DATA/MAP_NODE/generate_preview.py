import json
import xml.etree.ElementTree as ET

path_json = r'D:\Projects\FindMyCampus\findmycampus\data\campus_maps.json'
with open(path_json, 'r', encoding='utf-8') as f:
    data = json.load(f)

for m in data.get('maps', []):
    if m.get('id') == '500':
        nodes_500 = m.get('nodes', [])
    elif m.get('id') == '600':
        nodes_600 = m.get('nodes', [])

def create_overlay(svg_in, svg_out, nodes):
    # Read the SVG content
    with open(svg_in, 'r', encoding='utf-8') as f:
        svg_content = f.read()
    
    # We will just insert the circles and text right before the closing </svg> tag
    width = 2448
    height = 1584
    
    elements = ""
    for node in nodes:
        nx, ny = node.get('x', 0), node.get('y', 0)
        # Assuming nx, ny are percentages
        cx = (nx / 100.0) * width
        cy = (ny / 100.0) * height
        name = node.get('name', '')
        elements += f'<circle cx="{cx}" cy="{cy}" r="15" fill="red" stroke="black" stroke-width="2"/>\n'
        elements += f'<text x="{cx + 20}" y="{cy + 5}" fill="red" font-size="20" font-weight="bold" font-family="Arial">{name}</text>\n'
        
    svg_content = svg_content.replace('</svg>', elements + '</svg>')
    
    with open(svg_out, 'w', encoding='utf-8') as f:
        f.write(svg_content)

create_overlay(r'D:\Projects\FindMyCampus\findmycampus\data\Chennai, Tamil Nadu-1.svg',
               r'D:\Projects\FindMyCampus\findmycampus\data\500_preview.svg',
               nodes_500)
create_overlay(r'D:\Projects\FindMyCampus\findmycampus\data\Chennai, Tamil Nadu-2.svg',
               r'D:\Projects\FindMyCampus\findmycampus\data\600_preview.svg',
               nodes_600)
