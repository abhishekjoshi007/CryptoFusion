import json, pathlib, datetime as dt
from collections import defaultdict

ROOT = pathlib.Path(
    "/Users/abhishekjoshi/Documents/GitHub/"
    "Cross-Market-Deep-Learning-Multi-Modal-Stock-Crypto-Prediction/"
    "Historic Data Cry"
)

def load(p):
    with p.open(encoding="utf-8") as f:
        items = json.load(f)
    for obj in items:
        obj["Date"] = obj.pop("time", obj.get("Date"))
        obj.pop("source", None)
    return items

def merge(rows):
    buckets, seen = defaultdict(list), defaultdict(set)
    for r in rows:
        date = r.get("Date")
        txt  = ""
        if isinstance(r.get("content"), list) and r["content"]:
            txt = r["content"][0].get("text", "").strip()
        else:
            txt = str(r.get("text", "")).strip()
        if not (date and txt) or txt in seen[date]:
            continue
        r.pop("Date", None)
        buckets[date].append(r)
        seen[date].add(txt)
    to_dt = lambda s: dt.datetime.strptime(s, "%Y-%m-%d")
    return [{"Date": d, "comments": buckets[d]} for d in sorted(buckets, key=to_dt, reverse=True)]

for ticker_dir in ROOT.iterdir():
    if not ticker_dir.is_dir(): continue
    src_files = [p for p in ticker_dir.glob("*_comments.json") if "_merge_" not in p.name]
    if not src_files: continue
    merged = merge(sum((load(p) for p in src_files), []))
    (ticker_dir / f"{ticker_dir.name}_merge_comments.json").write_text(
        json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
    )
