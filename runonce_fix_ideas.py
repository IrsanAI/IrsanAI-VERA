import json
from pathlib import Path

f = Path(".tools/idea_graph.json")
data = json.loads(f.read_text(encoding="utf-8"))

seen = set()
clean = []
for idea in data["proposed"]:
    # Fix garbled UTF-8 encoding artifacts
    title = idea["title"]
    title = title.replace("\u00e2\u20ac\u201c", "\u2014")  # â€" → —
    title = title.replace("\u00e2\u20ac\u2122", "\u2019")  # â€™ → '
    title = title.strip()
    if title not in seen:
        seen.add(title)
        idea["title"] = title
        clean.append(idea)

data["proposed"] = clean
f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Cleaned: {len(clean)} unique ideas")
for i in clean:
    print(f"  {i['id']} — {i['title']}")
