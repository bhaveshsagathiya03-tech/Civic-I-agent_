"""Train a two-class CIVIC-I detector. Requires requirements-ml.txt and a labelled dataset."""
from pathlib import Path
import argparse
import yaml

REQUIRED = {0: "pothole", 1: "garbage_accumulation"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data.yaml")
    parser.add_argument("--model", default="yolo26n.pt")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default="cpu", help="cpu, 0, or mps")
    parser.add_argument("--name", default="civic_i_two_class")
    args = parser.parse_args()
    data_path = Path(args.data).resolve()
    if not data_path.is_file(): raise SystemExit(f"Dataset YAML not found: {data_path}")
    config = yaml.safe_load(data_path.read_text(encoding="utf-8"))
    names = config.get("names", {})
    names = {int(k): str(v) for k, v in names.items()} if isinstance(names, dict) else {i: str(v) for i, v in enumerate(names)}
    if names != REQUIRED:
        raise SystemExit(f"Class mapping must be exactly {REQUIRED}; received {names}")
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("Install optional ML dependencies: pip install -r requirements-ml.txt") from exc
    model = YOLO(args.model)
    model.train(data=str(data_path), epochs=args.epochs, imgsz=args.imgsz, batch=args.batch, device=args.device, name=args.name, project="runs/detect", patience=20, seed=42, deterministic=True)
    print("Training finished. Review validation metrics and local hold-out performance before deployment.")
    print("Best weights are normally written under runs/detect/<run-name>/weights/best.pt")

if __name__ == "__main__": main()
