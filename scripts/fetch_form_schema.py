import urllib.request
import re
import json

url = "https://docs.google.com/forms/d/e/1FAIpQLSeYRSeapl_kJ0TN_YVGIvCKRfwYCKZrI7xxq3AKzWJitesi1Q/viewform"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8')

# FB_PUBLIC_LOAD_DATA_ contains all question data and branching rules
match = re.search(r'FB_PUBLIC_LOAD_DATA_\s*=\s*(.*?);\s*</script>', html)
if match:
    data = json.loads(match.group(1))
    with open("scripts/form_schema.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Form schema saved, root length:", len(data))
    # data[1] is usually the form fields and pages
    form_desc = data[1][0] if len(data) > 1 and data[1] else "None"
    print("Form title:", form_desc)
    items = data[1][1] if len(data) > 1 and len(data[1]) > 1 else []
    print("Number of items:", len(items))
    for i, it in enumerate(items):
        title = it[1]
        item_type = it[3]
        print(f"Item {i}: id={it[0]}, title={title}, type={item_type}")
else:
    print("FB_PUBLIC_LOAD_DATA_ not found")
