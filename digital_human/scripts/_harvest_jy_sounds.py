"""收割剪映草稿音效 -> data/jy_sounds (语义命名 + 索引)."""
import glob
import json
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DRAFTS = r"C:\Users\tanhaox\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
DEST = r"F:\AI-Agent-Local\digital_human\data\jy_sounds"
os.makedirs(DEST, exist_ok=True)

seen: dict[str, str] = {}  # hash 文件名 -> 语义名
for tj in glob.glob(os.path.join(DRAFTS, "学习*", "template.json")) + \
          glob.glob(os.path.join(DRAFTS, "学习*", "Timelines", "*", "template.json")):
    try:
        data = json.load(open(tj, encoding="utf-8"))
    except Exception:
        continue
    for a in data.get("materials", {}).get("audios", []) or []:
        if a.get("type") != "sound":
            continue
        name = (a.get("name") or "").strip()
        p = a.get("path") or ""
        if not name or not p:
            continue
        seen.setdefault(os.path.basename(p), name)

copied: dict[str, int] = {}
for hashname, name in seen.items():
    src = None
    for cand in glob.glob(os.path.join(DRAFTS, "学习*", "materials", "audio", hashname)):
        src = cand
        break
    if not src:
        continue
    safe = "".join(c if c not in '\\/:*?"<>|' else "_" for c in name).strip() or hashname
    dst = os.path.join(DEST, safe + ".mp3")
    if not os.path.exists(dst):
        shutil.copy2(src, dst)
    copied[safe] = os.path.getsize(dst)

print(f"收割音效: {len(copied)} 个 -> {DEST}")
for n, s in sorted(copied.items()):
    print(f"  {s // 1024:>4}KB  {n}")
json.dump(copied, open(os.path.join(DEST, "_index.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
