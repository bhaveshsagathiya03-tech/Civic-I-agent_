"""Evaluate a trained CIVIC-I model on the held-out test split."""
from pathlib import Path
import argparse, json
import yaml

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--weights",required=True); parser.add_argument("--data",default="data.yaml"); parser.add_argument("--split",default="test",choices=["val","test"]); args=parser.parse_args()
    if not Path(args.weights).is_file(): raise SystemExit(f"Weights not found: {args.weights}")
    cfg=yaml.safe_load(Path(args.data).read_text(encoding="utf-8"))
    names=cfg.get("names",{}); names={int(k):str(v) for k,v in names.items()} if isinstance(names,dict) else {i:str(v) for i,v in enumerate(names)}
    if names != {0:"pothole",1:"garbage_accumulation"}: raise SystemExit("Dataset must use the exact CIVIC-I two-class mapping.")
    try:
        from ultralytics import YOLO
    except ImportError as exc: raise SystemExit("Install optional ML dependencies first.") from exc
    model=YOLO(args.weights)
    metrics=model.val(data=args.data,split=args.split,plots=True)
    result={"weights":str(Path(args.weights).resolve()),"data":str(Path(args.data).resolve()),"split":args.split,"metrics":{k:float(v) for k,v in metrics.results_dict.items()}}
    out=Path("evaluation_results.json"); out.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2)); print(f"Saved {out.resolve()}")

if __name__ == "__main__": main()
