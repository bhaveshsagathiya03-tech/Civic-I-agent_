# CIVIC-I model training

This folder contains the reproducible training/evaluation entry points for the two supported classes only.

## Required class mapping

```yaml
names:
  0: pothole
  1: garbage_accumulation
```

## 1. Create a YOLO dataset

Use the layout in `data.yaml.example`. Every image requires a matching `.txt` annotation file. Empty annotation files are valid negative examples. Annotation policy must consistently mark a pothole as a visible road cavity and garbage as a contiguous accumulation region.

RDD2022 can provide pothole imagery. Review its Pascal VOC annotations and map its D40 category to class 0. The supplied training scripts expect the final data already converted to YOLO format; they do not automatically convert or redistribute the original RDD2022 dataset.

TACO labels individual litter instances. Do not map all TACO litter boxes to garbage accumulation. Use it as contextual material only unless a qualified annotator creates valid accumulation-region labels.

## 2. Validate dataset syntax

```bash
python validate_dataset.py --data data.yaml
```

This validates file structure and annotation syntax. It does not establish annotation correctness, class balance, consent, licence compliance or data split independence.

## 3. Train

Install `../requirements-ml.txt`, then run:

```bash
python train.py --data data.yaml --model yolo26n.pt --epochs 100 --imgsz 640 --batch 8 --device cpu
```

Choose batch/device based on actual hardware. Do not assume CPU training will finish quickly.

## 4. Evaluate

```bash
python evaluate.py --weights runs/detect/civic_i_two_class/weights/best.pt --data data.yaml --split test
```

The script writes `evaluation_results.json` and Ultralytics validation plots. Preserve the exact dataset version, checkpoint, library versions and metrics.

## 5. Deploy

Copy the reviewed checkpoint to a protected backend model directory and set `YOLO_WEIGHTS` to its path. Check that `model.names` contains both exact target names. Restart the backend and check `/api/v1/models/status`.

Do not deploy until the checkpoint has been tested on a held-out Palghar-representative dataset and the Ultralytics licence has been reviewed.
