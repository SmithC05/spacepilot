import json
import re

path_json = r'D:\Projects\FindMyCampus\findmycampus\data\campus_maps.json'
with open(path_json, 'r', encoding='utf-8') as f:
    data = json.load(f)

nodes_500 = []
nodes_600 = []
svg_500_path = r'D:\Projects\FindMyCampus\findmycampus\data\Chennai, Tamil Nadu-1.svg'
svg_600_path = r'D:\Projects\FindMyCampus\findmycampus\data\Chennai, Tamil Nadu-2.svg'

for m in data.get('maps', []):
    if m.get('id') == '500':
        nodes_500 = m.get('nodes', [])
    elif m.get('id') == '600':
        nodes_600 = m.get('nodes', [])

def get_svg_content(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Remove the xml declaration if present
    content = re.sub(r'<\?xml.*?\?>', '', content)
    # Give the SVG a class so we can target it
    content = content.replace('<svg ', '<svg class="map-svg" preserveAspectRatio="xMidYMid meet" ')
    return content

svg_500 = get_svg_content(svg_500_path)
svg_600 = get_svg_content(svg_600_path)

html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Campus 2.5D Viewer</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0f172a;
            --glass-bg: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(255, 255, 255, 0.1);
            --accent: #3b82f6;
            --accent-glow: rgba(59, 130, 246, 0.6);
            --node-color: #2dd4bf;
            --node-glow: rgba(45, 212, 191, 0.8);
        }}
        body {{
            margin: 0;
            padding: 0;
            background: var(--bg-color);
            background-image: 
                radial-gradient(at 0% 0%, rgba(30, 58, 138, 0.4) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(17, 24, 39, 0.8) 0px, transparent 50%);
            color: white;
            font-family: 'Inter', sans-serif;
            overflow: hidden;
            display: flex;
            height: 100vh;
            width: 100vw;
        }}
        
        .sidebar {{
            width: 350px;
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-right: 1px solid var(--glass-border);
            padding: 2rem;
            display: flex;
            flex-direction: column;
            z-index: 10;
            box-shadow: 4px 0 24px rgba(0,0,0,0.2);
        }}

        h1 {{
            font-size: 1.5rem;
            font-weight: 800;
            margin-top: 0;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #60a5fa, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        p.subtitle {{
            color: #94a3b8;
            font-size: 0.875rem;
            margin-bottom: 2rem;
        }}

        .info-card {{
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-top: 2rem;
            opacity: 0;
            transform: translateY(10px);
            transition: all 0.4s ease;
        }}

        .info-card.active {{
            opacity: 1;
            transform: translateY(0);
        }}

        .info-card h2 {{
            margin: 0 0 0.5rem 0;
            font-size: 1.25rem;
            color: white;
        }}

        .info-card p {{
            margin: 0;
            color: #cbd5e1;
            font-size: 0.9rem;
        }}

        .controls {{
            margin-top: auto;
            display: flex;
            gap: 1rem;
        }}

        button {{
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            color: white;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            flex: 1;
        }}

        button:hover, button.active {{
            background: var(--accent);
            border-color: var(--accent);
            box-shadow: 0 0 16px var(--accent-glow);
        }}

        .map-container {{
            flex: 1;
            position: relative;
            perspective: 2000px; /* Strong perspective for isometric feel */
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: grab;
        }}

        .map-container:active {{
            cursor: grabbing;
        }}

        .iso-scene {{
            width: 1200px;
            height: 800px;
            position: relative;
            /* 2.5D Isometric Transform */
            transform: rotateX(60deg) rotateZ(-45deg) translateZ(0);
            transform-style: preserve-3d;
            transition: transform 0.1s linear; /* Smooth panning */
        }}

        .map-layer {{
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.5s ease;
        }}

        .map-layer.active {{
            opacity: 1;
            pointer-events: auto;
        }}

        .map-svg {{
            width: 100%;
            height: 100%;
            position: absolute;
            top: 0;
            left: 0;
            /* Create the 3D extrusion effect using stacked drop-shadows */
            filter: 
                drop-shadow(-1px 1px 0px #1e293b)
                drop-shadow(-2px 2px 0px #1e293b)
                drop-shadow(-3px 3px 0px #1e293b)
                drop-shadow(-4px 4px 0px #1e293b)
                drop-shadow(-5px 5px 0px #1e293b)
                drop-shadow(-6px 6px 0px #0f172a)
                drop-shadow(-12px 12px 24px rgba(0,0,0,0.8));
        }}

        .node {{
            position: absolute;
            width: 16px;
            height: 16px;
            background: var(--node-color);
            border-radius: 50%;
            transform: translate(-50%, -50%) translateZ(20px) rotateX(-90deg);
            box-shadow: 0 0 12px var(--node-glow);
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            z-index: 100;
        }}
        
        /* Inner pulse effect */
        .node::after {{
            content: '';
            position: absolute;
            top: -4px; left: -4px; right: -4px; bottom: -4px;
            border: 2px solid var(--node-color);
            border-radius: 50%;
            animation: pulse 2s infinite;
            opacity: 0.5;
        }}

        @keyframes pulse {{
            0% {{ transform: scale(1); opacity: 0.8; }}
            100% {{ transform: scale(2); opacity: 0; }}
        }}

        .node:hover, .node.active {{
            transform: translate(-50%, -50%) translateZ(40px) rotateX(-90deg) scale(1.5);
            background: white;
            box-shadow: 0 0 24px var(--node-glow), 0 0 40px white;
        }}

        .node-label {{
            position: absolute;
            left: 50%;
            bottom: 150%;
            transform: translateX(-50%);
            background: rgba(15, 23, 42, 0.9);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s ease, bottom 0.3s ease;
            white-space: nowrap;
            border: 1px solid var(--glass-border);
        }}

        .node:hover .node-label {{
            opacity: 1;
            bottom: 180%;
        }}

    </style>
</head>
<body>

    <div class="sidebar">
        <h1>Smart Campus Map</h1>
        <p class="subtitle">2.5D Interactive Viewer</p>

        <div class="controls">
            <button id="btn-500" class="active" onclick="switchMap('500')">500 Series</button>
            <button id="btn-600" onclick="switchMap('600')">600 Series</button>
        </div>

        <div class="info-card" id="info-card">
            <h2 id="info-title">Select a Room</h2>
            <p id="info-desc">Click on any glowing node on the 3D map to view its details.</p>
        </div>
    </div>

    <div class="map-container" id="map-container">
        <div class="iso-scene" id="iso-scene">
            <!-- 500 Series Layer -->
            <div class="map-layer active" id="layer-500">
                {svg_500}
                <div id="nodes-500"></div>
            </div>

            <!-- 600 Series Layer -->
            <div class="map-layer" id="layer-600">
                {svg_600}
                <div id="nodes-600"></div>
            </div>
        </div>
    </div>

    <script>
        const nodes500 = {json.dumps(nodes_500)};
        const nodes600 = {json.dumps(nodes_600)};

        function renderNodes(containerId, nodes) {{
            const container = document.getElementById(containerId);
            container.innerHTML = '';
            
            nodes.forEach(node => {{
                if (node.type === "ROOM" || node.type === "GATEWAY") {{
                    const el = document.createElement('div');
                    el.className = 'node';
                    el.style.left = node.x + '%';
                    el.style.top = node.y + '%';
                    
                    const label = document.createElement('div');
                    label.className = 'node-label';
                    label.textContent = node.name;
                    el.appendChild(label);
                    
                    el.onclick = (e) => {{
                        e.stopPropagation();
                        // Reset all nodes
                        document.querySelectorAll('.node').forEach(n => n.classList.remove('active'));
                        el.classList.add('active');
                        
                        // Update info card
                        const card = document.getElementById('info-card');
                        document.getElementById('info-title').textContent = node.name;
                        document.getElementById('info-desc').textContent = `Type: ${{node.type}}\\nCategory: ${{node.category}}\\nCoordinates: (${{node.x}}, ${{node.y}})`;
                        card.classList.add('active');
                    }};
                    
                    container.appendChild(el);
                }}
            }});
        }}

        renderNodes('nodes-500', nodes500);
        renderNodes('nodes-600', nodes600);

        function switchMap(mapId) {{
            // Update buttons
            document.getElementById('btn-500').classList.remove('active');
            document.getElementById('btn-600').classList.remove('active');
            document.getElementById(`btn-${{mapId}}`).classList.add('active');

            // Update layers
            document.getElementById('layer-500').classList.remove('active');
            document.getElementById('layer-600').classList.remove('active');
            document.getElementById(`layer-${{mapId}}`).classList.add('active');
            
            // Reset info card
            document.getElementById('info-card').classList.remove('active');
        }}

        // Simple Drag to Pan the Map
        let isDragging = false;
        let startX, startY;
        let transX = 0, transY = 0;
        const scene = document.getElementById('iso-scene');
        const container = document.getElementById('map-container');

        container.addEventListener('mousedown', (e) => {{
            isDragging = true;
            startX = e.clientX - transX;
            startY = e.clientY - transY;
        }});

        window.addEventListener('mouseup', () => {{
            isDragging = false;
        }});

        window.addEventListener('mousemove', (e) => {{
            if (!isDragging) return;
            transX = e.clientX - startX;
            transY = e.clientY - startY;
            scene.style.transform = `rotateX(60deg) rotateZ(-45deg) translateZ(0) translate(${{transX}}px, ${{transY}}px)`;
        }});
        
        // Initial transform applied
        scene.style.transform = `rotateX(60deg) rotateZ(-45deg) translateZ(0) translate(0px, 0px)`;
    </script>
</body>
</html>
"""

with open(r'D:\Projects\FindMyCampus\findmycampus\data\2.5d_map_viewer.html', 'w', encoding='utf-8') as f:
    f.write(html_template)

print("Generated 2.5d_map_viewer.html successfully!")
