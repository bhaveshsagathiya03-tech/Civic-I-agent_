# CIVIC-I data and model plan

## Exact target classes

| ID | Name | Annotation meaning |
|---|---|---|
| 0 | `pothole` | A visible pothole/road cavity, not a shadow, road patch or manhole cover. |
| 1 | `garbage_accumulation` | A visible contiguous accumulation/dumping area, not an isolated wrapper or ordinary bin. |

The target task is object detection. Every bounding box must cover the target region according to a written annotation guide. Ambiguous images should be excluded or labelled for review rather than forced into a class.

## Candidate datasets

### Road damage

RDD2022 is a candidate starting point. Its official challenge page describes India training images and the D40 pothole class among the four challenge categories. Its GitHub release includes Pascal VOC XML annotations. Download only the country-specific data actually required, preserve the original annotations, inspect the source licence and cite the dataset paper. The dataset is not a Palghar validation set.

- Dataset information: https://crddc2022.sekilab.global/data/
- Official release repository: https://github.com/sekilab/RoadDamageDetector
- Dataset paper DOI: https://doi.org/10.1002/gdj3.260

RDD2022 images include different capture styles; the dataset page notes that China contains top-down/oblique images, unlike the road-parallel vehicle-mounted imagery used for several other countries. Inspect and curate the Indian subset and do not assume all images match the intended citizen-upload setting.

### Garbage

TACO (Trash Annotations in Context) contains manually annotated litter instances and COCO-format annotations. It can provide useful context or pretraining material, but its labels generally identify individual litter objects. That is not the same as a single `garbage_accumulation` region. Do not map every TACO object box directly to the accumulation class. Build a separate accumulation-region dataset with human-reviewed bounding boxes, including Palghar-like street dumping, roadside piles and public waste hotspots.

- Official repository: https://github.com/pedropro/TACO
- Dataset record: https://zenodo.org/records/3587843

Check current dataset terms and image rights at the source before using or redistributing any data. A dataset's availability does not automatically grant every intended use.

## Required folder format

Prepare a YOLO-format dataset:

```text
civic-i-dataset/
  images/
    train/
    val/
    test/
  labels/
    train/
    val/
    test/
  data.yaml
```

Each label row must use:

```text
class_id x_center y_center width height
```

Coordinates must be normalised to [0,1]. Class IDs must be exactly 0 and 1 as defined above. Include negative images with empty label files if neither supported issue is present.

Do not place near-identical frames or photos of the same physical scene in different data splits. Split by capture session, source route or location where possible to reduce leakage.

## Model choice and licensing

The current Ultralytics documentation presents YOLO26 as its current model family and documents custom training with `YOLO("yolo26n.pt")` followed by `.train(...)`. CIVIC-I starts with the small `yolo26n` model as a candidate for an affordable prototype, but the final choice must be measured on the target hardware and held-out Palghar images.

Ultralytics currently offers AGPL-3.0 and Enterprise licensing. Before a closed-source, hosted or municipal deployment, obtain a legal/licensing review and determine whether AGPL obligations are acceptable or an Enterprise licence is required. Dataset licences are separate from model/software licences.

- Model docs: https://docs.ultralytics.com/models/yolo26/
- Training docs: https://docs.ultralytics.com/modes/train/
- Licence: https://www.ultralytics.com/license

## Local validation

Collect representative images with consent and avoid unnecessary identifiable people, vehicle plates or private property. Label potholes and garbage accumulation separately. Include hard negatives such as shadows, tar patches, manhole covers, wet reflections, isolated litter and empty roads.

Report precision, recall, F1, mAP50, mAP50-95, confusion matrix, latency and false positive/negative examples separately for each class. A model is not deployment-ready merely because training completed.
