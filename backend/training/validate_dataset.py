"""Validate a YOLO-format dataset for the exact CIVIC-I two-class mapping."""
from pathlib import Path
import argparse
import yaml

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}

def validate_split(root: Path, split: str):
    image_dir = root / "images" / split
    label_dir = root / "labels" / split
    if not image_dir.is_dir() or not label_dir.is_dir():
        raise ValueError(f"Missing images/{split} or labels/{split} under {root}")
    images = [p for p in image_dir.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES]
    missing, malformed, counts = [], [], {0: 0, 1: 0}
    for image in images:
        label = label_dir / f"{image.stem}.txt"
        if not label.exists():
            missing.append(image.name); continue
        for line_no, line in enumerate(label.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip(): continue
            parts = line.split()
            try:
                if len(parts) != 5: raise ValueError("expected 5 columns")
                cls = int(parts[0]); coords = [float(v) for v in parts[1:]]
                if cls not in counts: raise ValueError(f"unsupported class {cls}")
                if any(v < 0 or v > 1 for v in coords): raise ValueError("normalised coordinate outside [0,1]")
                if coords[2] <= 0 or coords[3] <= 0: raise ValueError("non-positive box size")
                counts[cls] += 1
            except Exception as exc: malformed.append(f"{label.name}:{line_no}: {exc}")
    return {"images": len(images), "missing_label_files": missing, "malformed_lines": malformed, "class_counts": counts}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--data",default="data.yaml"); args=parser.parse_args()
    cfg=yaml.safe_load(Path(args.data).read_text(encoding="utf-8")); root=Path(cfg.get("path",Path(args.data).parent)).resolve()
    names=cfg.get("names",{}); names={int(k):str(v) for k,v in names.items()} if isinstance(names,dict) else {i:str(v) for i,v in enumerate(names)}
    expected={0:"pothole",1:"garbage_accumulation"}
    if names != expected: raise SystemExit(f"Expected exact class mapping {expected}, received {names}")
    failed=False
    for split in ("train","val","test"):
        if split not in cfg: continue
        result=validate_split(root,split)
        print(f"\n[{split}] images={result['images']} class_counts={result['class_counts']}")
        if result['missing_label_files']: print("Missing labels:", result['missing_label_files'][:20]); failed=True
        if result['malformed_lines']: print("Malformed:", result['malformed_lines'][:20]); failed=True
        if result['images']==0: failed=True
    if failed: raise SystemExit("Dataset validation failed. Correct the issues before training.")
    print("Dataset structure and label syntax passed. This does not establish annotation quality or absence of data leakage.")

if __name__ == "__main__": main()
