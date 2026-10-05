import re
from pathlib import Path

content = Path("frontend/app.js").read_text(encoding="utf-8")
onclicks = set(re.findall(r'onclick=["\']([a-zA-Z0-9_]+)\(', content))
print(f"Total onclick functions: {len(onclicks)}")
for fn in sorted(onclicks):
    m = re.search(r'(?:async\s+)?function\s+' + fn + r'\s*\([^)]*\)\s*\{([\s\S]*?)\n\}', content)
    if m:
        body = m.group(1).strip()
        has_state = "state." in body
        has_api = "api(" in body or "fetch(" in body
        has_render = "render(" in body
        has_dom = "document." in body or "$(" in body
        has_toast = "toast(" in body
        has_export = "export" in body.lower()
        has_nav = "showView(" in body or "renderSlide(" in body or "close" in body or "executeDemoStep(" in body
        if not (has_state or has_api or has_render or has_dom or has_export or has_nav):
            clean_b = body[:120].encode('ascii', errors='replace').decode('ascii')
            print(f"SUSPECT (NO EFFECT): {fn} -> {clean_b}")
        elif has_toast and not (has_state or has_api or has_render or has_export or has_nav or has_dom):
            clean_b = body[:120].encode('ascii', errors='replace').decode('ascii')
            print(f"TOAST ONLY: {fn} -> {clean_b}")
