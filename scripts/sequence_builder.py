# -*- coding: utf-8 -*-
"""
Enhanced SVG Sequence Diagram Generator for T-Lingua thesis report.
Matches Visual Paradigm / Enterprise Architect UML standard with Robustness Analysis Icons:
- Actor (Stick figure)
- Boundary (|O)
- Control (Circle with top curved arrow)
- Entity (_O_)
- Database (Cylinder)
- Worker (Drop-shadowed component box)
Includes continuous activation bar merging, dynamic diagram height, responsive horizontal spacing,
and combined fragments (alt / opt / loop).
Zero internal title banner, zero watermark.
"""
import os
import subprocess

IMG_DIR = r"C:\Du_an\T_Langua_Test\docs\img\tt"
os.makedirs(IMG_DIR, exist_ok=True)
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

class SequenceDiagram:
    def __init__(self, width=None, min_height=400):
        self.user_width = width
        self.min_height = min_height
        self.lifelines = [] # list of dicts: id, name, type, x
        self.events = []
        
    def add_lifeline(self, id_str, name, l_type="control"):
        """
        l_type can be: 'actor', 'boundary', 'control', 'entity', 'database', 'worker'
        """
        self.lifelines.append({
            "id": id_str,
            "name": name,
            "type": l_type,
            "x": 0
        })
        
    def message(self, from_id, to_id, label, is_return=False):
        self.events.append({
            "type": "msg",
            "from": from_id,
            "to": to_id,
            "label": label,
            "is_return": is_return
        })

    def self_message(self, target_id, label):
        self.events.append({
            "type": "self_msg",
            "target": target_id,
            "label": label
        })

    def frame_start(self, frame_type, condition, from_id=None, to_id=None):
        self.events.append({
            "type": "frame_start",
            "frame_type": frame_type, # 'alt', 'opt', 'loop', 'par'
            "condition": condition,
            "from": from_id,
            "to": to_id
        })

    def frame_else(self, condition="else"):
        self.events.append({
            "type": "frame_else",
            "condition": condition
        })

    def frame_end(self):
        self.events.append({
            "type": "frame_end"
        })

    def render_svg(self):
        n = len(self.lifelines)
        if self.user_width:
            width = self.user_width
        else:
            if n <= 4:
                width = 880
            elif n <= 6:
                width = 1040
            elif n <= 7:
                width = 1180
            else:
                width = 1320

        margin_x = 75
        spacing = (width - 2 * margin_x) / max(1, (n - 1)) if n > 1 else width / 2
        for i, ll in enumerate(self.lifelines):
            ll["x"] = int(margin_x + i * spacing)
            
        header_y = 65
        line_start_y = 110
        y_step = 32
        
        ll_map = {ll["id"]: ll["x"] for ll in self.lifelines}
        
        # 1. First Pass: Compute Y coordinates for all events and track activation intervals
        cur_y = line_start_y + 30
        event_layouts = []
        raw_activations = {ll["id"]: [] for ll in self.lifelines}
        
        for ev in self.events:
            ev_type = ev["type"]
            
            if ev_type == "msg":
                f_id = ev["from"]
                t_id = ev["to"]
                x1 = ll_map[f_id]
                x2 = ll_map[t_id]
                event_layouts.append({
                    "ev": ev,
                    "y": cur_y,
                    "x1": x1,
                    "x2": x2
                })
                # record active interval for endpoints
                raw_activations[f_id].append((cur_y - 8, cur_y + 8))
                raw_activations[t_id].append((cur_y - 8, cur_y + 8))
                cur_y += y_step
                
            elif ev_type == "self_msg":
                t_id = ev["target"]
                x = ll_map[t_id]
                loop_h = 18
                event_layouts.append({
                    "ev": ev,
                    "y": cur_y,
                    "x": x,
                    "h": loop_h
                })
                raw_activations[t_id].append((cur_y - 6, cur_y + loop_h + 8))
                cur_y += loop_h + 16
                
            elif ev_type == "frame_start":
                from_id = ev.get("from")
                to_id = ev.get("to")
                if from_id and to_id:
                    fx1 = min(ll_map[from_id], ll_map[to_id]) - 35
                    fx2 = max(ll_map[from_id], ll_map[to_id]) + 35
                else:
                    fx1 = margin_x - 35
                    fx2 = width - margin_x + 35
                event_layouts.append({
                    "ev": ev,
                    "y": cur_y,
                    "fx1": fx1,
                    "fx2": fx2
                })
                cur_y += 34
                
            elif ev_type == "frame_else":
                event_layouts.append({
                    "ev": ev,
                    "y": cur_y
                })
                cur_y += 30
                
            elif ev_type == "frame_end":
                event_layouts.append({
                    "ev": ev,
                    "y": cur_y
                })
                cur_y += 24
                
        total_height = max(self.min_height, cur_y + 35)
        bottom_y = total_height - 25

        # Merge close activations for each lifeline
        merged_activations = {}
        for l_id, intervals in raw_activations.items():
            if not intervals:
                merged_activations[l_id] = []
                continue
            intervals.sort(key=lambda item: item[0])
            merged = []
            curr_start, curr_end = intervals[0]
            for s, e in intervals[1:]:
                # If gap is small (<= 45px), merge into continuous bar
                if s <= curr_end + 45:
                    curr_end = max(curr_end, e)
                else:
                    merged.append((curr_start, curr_end))
                    curr_start, curr_end = s, e
            merged.append((curr_start, curr_end))
            merged_activations[l_id] = merged

        # 2. Build SVG markup
        svg_parts = []
        svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {total_height}" width="{width}" height="{total_height}" style="background-color: #FFFFFF; font-family: Segoe UI, Arial, sans-serif;">')
        
        # Defs: Markers for arrows
        svg_parts.append("""
        <defs>
          <marker id="arrow-sync" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#1E293B"/>
          </marker>
          <marker id="arrow-return" viewBox="0 0 10 10" refX="0" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <polyline points="9,1.5 0,5 9,8.5" fill="none" stroke="#475569" stroke-width="1.6"/>
          </marker>
          <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%" filterUnits="userSpaceOnUse">
            <feDropShadow dx="1" dy="1.5" stdDeviation="1.5" flood-color="#000000" flood-opacity="0.1"/>
          </filter>
        </defs>
        """)

        # Lifeline vertical dashed lines
        for ll in self.lifelines:
            x = ll["x"]
            svg_parts.append(f'<line x1="{x}" y1="{line_start_y}" x2="{x}" y2="{bottom_y}" stroke="#94A3B8" stroke-width="1.2" stroke-dasharray="4,4"/>')

        # Draw merged activation rectangles
        for ll in self.lifelines:
            x = ll["x"]
            for (s_y, e_y) in merged_activations.get(ll["id"], []):
                h = max(18, e_y - s_y)
                svg_parts.append(f'<rect x="{x - 5}" y="{s_y}" width="10" height="{h}" fill="#F8FAFC" stroke="#334155" stroke-width="1.2" rx="1"/>')

        # Process frames and messages
        frame_stack = []
        
        for item in event_layouts:
            ev = item["ev"]
            ev_type = ev["type"]
            y = item["y"]
            
            if ev_type == "msg":
                x1 = item["x1"]
                x2 = item["x2"]
                lbl = ev["label"]
                is_ret = ev["is_return"]
                
                # Adjust line endpoints to stop at activation bar edges
                if x1 < x2:
                    start_x = x1 + 5
                    end_x = x2 - 5
                else:
                    start_x = x1 - 5
                    end_x = x2 + 5
                    
                mid_x = (start_x + end_x) / 2
                
                if is_ret:
                    svg_parts.append(f'<line x1="{start_x}" y1="{y}" x2="{end_x}" y2="{y}" stroke="#475569" stroke-width="1.2" stroke-dasharray="4,3" marker-end="url(#arrow-return)"/>')
                    svg_parts.append(f'<text x="{mid_x}" y="{y - 4}" font-size="9.5" fill="#475569" font-style="italic" text-anchor="middle" paint-order="stroke fill" stroke="#FFFFFF" stroke-width="4px" stroke-linejoin="round">{lbl}</text>')
                else:
                    svg_parts.append(f'<line x1="{start_x}" y1="{y}" x2="{end_x}" y2="{y}" stroke="#1E293B" stroke-width="1.3" marker-end="url(#arrow-sync)"/>')
                    svg_parts.append(f'<text x="{mid_x}" y="{y - 5}" font-size="10" font-weight="600" fill="#0F172A" text-anchor="middle" paint-order="stroke fill" stroke="#FFFFFF" stroke-width="4px" stroke-linejoin="round">{lbl}</text>')

            elif ev_type == "self_msg":
                x = item["x"]
                h = item["h"]
                lbl = ev["label"]
                loop_w = 26
                svg_parts.append(f'<polyline points="{x+5},{y} {x+5+loop_w},{y} {x+5+loop_w},{y+h} {x+5},{y+h}" fill="none" stroke="#1E293B" stroke-width="1.3" marker-end="url(#arrow-sync)"/>')
                svg_parts.append(f'<text x="{x + loop_w + 12}" y="{y + 12}" font-size="9.8" font-weight="600" fill="#0F172A">{lbl}</text>')

            elif ev_type == "frame_start":
                frame_stack.append({
                    "start_y": y,
                    "type": ev["frame_type"],
                    "cond": ev["condition"],
                    "x1": item["fx1"],
                    "x2": item["fx2"],
                    "else_list": []
                })

            elif ev_type == "frame_else":
                if frame_stack:
                    frame_stack[-1]["else_list"].append((y, ev["condition"]))

            elif ev_type == "frame_end":
                if frame_stack:
                    f = frame_stack.pop()
                    start_y = f["start_y"]
                    end_y = y + 16
                    fx1 = f["x1"]
                    fx2 = f["x2"]
                    fw = fx2 - fx1
                    fh = end_y - start_y
                    
                    svg_parts.append(f'<rect x="{fx1}" y="{start_y}" width="{fw}" height="{fh}" fill="#F8FAFC" fill-opacity="0.3" stroke="#475569" stroke-width="1.1"/>')
                    badge_w = 38
                    badge_h = 16
                    svg_parts.append(f'<polygon points="{fx1},{start_y} {fx1+badge_w},{start_y} {fx1+badge_w+6},{start_y+badge_h/2} {fx1+badge_w},{start_y+badge_h} {fx1},{start_y+badge_h}" fill="#E2E8F0" stroke="#475569" stroke-width="1"/>')
                    svg_parts.append(f'<text x="{fx1+6}" y="{start_y+12}" font-size="9.5" font-weight="bold" fill="#1E293B">{f["type"]}</text>')
                    if f["cond"]:
                        svg_parts.append(f'<text x="{fx1+badge_w+14}" y="{start_y+12}" font-size="9.5" font-weight="600" font-style="italic" fill="#0284C7">[{f["cond"]}]</text>')
                        
                    for (ey, econd) in f["else_list"]:
                        svg_parts.append(f'<line x1="{fx1}" y1="{ey}" x2="{fx2}" y2="{ey}" stroke="#64748B" stroke-width="1.1" stroke-dasharray="4,4"/>')
                        if econd:
                            svg_parts.append(f'<text x="{fx1+12}" y="{ey+13}" font-size="9.5" font-weight="600" font-style="italic" fill="#DC2626">[{econd}]</text>')

        # 3. Draw Lifeline Headers (Icons and Text) on top of lines
        for ll in self.lifelines:
            x = ll["x"]
            y = header_y
            name = ll["name"]
            l_type = ll["type"]
            
            if l_type == "actor":
                svg_parts.append(f'<circle cx="{x}" cy="{y-24}" r="7" fill="#FFFFFF" stroke="#1E293B" stroke-width="1.5"/>')
                svg_parts.append(f'<line x1="{x}" y1="{y-17}" x2="{x}" y2="{y-3}" stroke="#1E293B" stroke-width="1.5"/>')
                svg_parts.append(f'<line x1="{x-11}" y1="{y-12}" x2="{x+11}" y2="{y-12}" stroke="#1E293B" stroke-width="1.5"/>')
                svg_parts.append(f'<line x1="{x}" y1="{y-3}" x2="{x-9}" y2="{y+10}" stroke="#1E293B" stroke-width="1.5"/>')
                svg_parts.append(f'<line x1="{x}" y1="{y-3}" x2="{x+9}" y2="{y+10}" stroke="#1E293B" stroke-width="1.5"/>')
                svg_parts.append(f'<text x="{x}" y="{y+26}" font-size="10.5" font-weight="bold" fill="#0F172A" text-anchor="middle">{name}</text>')

            elif l_type == "boundary":
                svg_parts.append(f'<circle cx="{x}" cy="{y-6}" r="14" fill="#FFFFFF" stroke="#1E293B" stroke-width="1.6"/>')
                svg_parts.append(f'<line x1="{x-14}" y1="{y-20}" x2="{x-14}" y2="{y+8}" stroke="#1E293B" stroke-width="2"/>')
                svg_parts.append(f'<line x1="{x-14}" y1="{y-6}" x2="{x}" y2="{y-6}" stroke="#1E293B" stroke-width="1.6"/>')
                svg_parts.append(f'<text x="{x}" y="{y+24}" font-size="10.5" font-weight="bold" fill="#0F172A" text-anchor="middle">{name}</text>')

            elif l_type == "control":
                svg_parts.append(f'<circle cx="{x}" cy="{y-6}" r="14" fill="#FFFFFF" stroke="#1E293B" stroke-width="1.6"/>')
                svg_parts.append(f'<path d="M {x-4} {y-20} L {x+4} {y-20} L {x} {y-26} z" fill="#1E293B"/>')
                svg_parts.append(f'<text x="{x}" y="{y+24}" font-size="10.5" font-weight="bold" fill="#0F172A" text-anchor="middle">{name}</text>')

            elif l_type == "entity":
                svg_parts.append(f'<circle cx="{x}" cy="{y-6}" r="14" fill="#FFFFFF" stroke="#1E293B" stroke-width="1.6"/>')
                svg_parts.append(f'<line x1="{x-14}" y1="{y+8}" x2="{x+14}" y2="{y+8}" stroke="#1E293B" stroke-width="2"/>')
                svg_parts.append(f'<text x="{x}" y="{y+24}" font-size="10.5" font-weight="bold" fill="#0F172A" text-anchor="middle">{name}</text>')

            elif l_type == "database":
                db_w = 26
                db_h = 24
                r_top = 4
                svg_parts.append(f'<ellipse cx="{x}" cy="{y-12}" rx="{db_w/2}" ry="{r_top}" fill="#FFFFFF" stroke="#1E293B" stroke-width="1.4"/>')
                svg_parts.append(f'<path d="M {x-db_w/2} {y-12} L {x-db_w/2} {y+6} A {db_w/2} {r_top} 0 0 0 {x+db_w/2} {y+6} L {x+db_w/2} {y-12}" fill="#FFFFFF" stroke="#1E293B" stroke-width="1.4"/>')
                svg_parts.append(f'<ellipse cx="{x}" cy="{y+6}" rx="{db_w/2}" ry="{r_top}" fill="none" stroke="#1E293B" stroke-width="1.4"/>')
                svg_parts.append(f'<text x="{x}" y="{y+24}" font-size="10.5" font-weight="bold" fill="#0F172A" text-anchor="middle">{name}</text>')

            else: # Worker / Generic Component box
                box_w = 110
                box_h = 28
                svg_parts.append(f'<rect x="{x-box_w/2}" y="{y-18}" width="{box_w}" height="{box_h}" rx="3" fill="#FFFFFF" stroke="#1E293B" stroke-width="1.4"/>')
                svg_parts.append(f'<text x="{x}" y="{y}" font-size="9.5" font-weight="bold" fill="#0F172A" text-anchor="middle">{name}</text>')

        self.last_width = width
        self.last_height = total_height
        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    def export_png(self, output_path):
        svg_content = self.render_svg()
        w = getattr(self, 'last_width', 1100) + 20
        h = getattr(self, 'last_height', 600) + 20
        html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{
    background: #FFFFFF !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 8px !important;
    width: {w}px !important;
    height: {h}px !important;
}}
::-webkit-scrollbar {{
    display: none !important;
    width: 0 !important;
    height: 0 !important;
}}
</style></head><body>{svg_content}</body></html>"""
        
        tmp_html = output_path.replace(".png", "_temp.html")
        with open(tmp_html, "w", encoding="utf-8") as f:
            f.write(html)
            
        cmd = [
            CHROME_PATH,
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--screenshot={output_path}",
            f"--window-size={w},{h}",
            f"file:///{tmp_html}"
        ]
        subprocess.run(cmd, capture_output=True)
        if os.path.exists(tmp_html):
            try:
                os.remove(tmp_html)
            except Exception:
                pass
        print(f"Rendered: {output_path} ({os.path.getsize(output_path)/1024:.1f} KB)")
