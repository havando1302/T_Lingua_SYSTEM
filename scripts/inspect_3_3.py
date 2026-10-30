# -*- coding: utf-8 -*-
import re

with open('scripts/section_3_3_sequences.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Split by captions
parts = re.split(r'add_caption\(doc,\s*"Hình (3\.\d+): ([^"]+)"', text)
print(f"Parts count: {len(parts)}")

# The split produces: [preamble, fig_no1, title1, content1, fig_no2, title2, content2, ...]
for i in range(1, len(parts), 3):
    fig_no = parts[i]
    title = parts[i+1]
    content = parts[i+2]
    
    # Extract table steps
    steps = re.findall(r'\("(\d+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)', content)
    print(f"\nHình {fig_no}: {title} -> {len(steps)} steps")
    if steps:
        senders = set(s[1] for s in steps)
        receivers = set(s[2] for s in steps)
        all_actors = sorted(list(senders.union(receivers)))
        print(f"   Lifelines ({len(all_actors)}): {', '.join(all_actors)}")
