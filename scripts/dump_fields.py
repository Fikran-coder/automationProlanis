import json

with open("scripts/form_schema.json", "r") as f:
    schema = json.load(f)

# Inspect exact structure of questions and choices
items = schema[1][1]
for it in items:
    title = it[1]
    itype = it[3]
    details = it[4]
    entry_id = details[0][0] if details else None
    choices = [c[0] for c in details[0][1]] if (details and len(details[0]) > 1 and details[0][1]) else []
    print(f"Title: {title!r}")
    print(f"  type={itype}, entry={entry_id}, choices={choices}")
