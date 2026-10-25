import json

with open("scripts/form_schema.json", "r", encoding="utf-8") as f:
    data = json.load(f)

items = data[1][1]
pages = []
current_page = {"index": 1, "title": "Page 1", "items": []}

for it in items:
    item_id = it[0]
    title = it[1]
    itype = it[3]
    if itype == 8: # Page break
        pages.append(current_page)
        current_page = {"index": len(pages) + 1, "title": title, "page_break_id": item_id, "items": []}
    else:
        # Extract choices and entry id
        details = it[4] if len(it) > 4 and it[4] else []
        entry_id = None
        choices = []
        if details:
            entry_id = details[0][0]
            if len(details[0]) > 1 and details[0][1]:
                raw_choices = details[0][1]
                for c in raw_choices:
                    val = c[0]
                    # check if branching is present: c[2] or c[4] or similar
                    target = c[2] if len(c) > 2 else None
                    choices.append((val, target))
        current_page["items"].append({
            "id": item_id,
            "title": title,
            "type": itype,
            "entry_id": entry_id,
            "choices": choices
        })
pages.append(current_page)

for p in pages:
    print(f"=== PAGE {p['index']}: {p['title']} ===")
    for it in p["items"]:
        print(f"  Field: {it['title']} (entry.{it['entry_id']}, type={it['type']})")
        if it['choices']:
            print(f"    Choices: {it['choices']}")
