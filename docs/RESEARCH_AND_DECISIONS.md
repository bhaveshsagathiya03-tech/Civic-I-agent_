# CIVIC-I — Research and Engineering Decisions

Research snapshot: 6 November 2026. Re-check vendor documentation, licensing and government rules before a public deployment.

## 1. Computer vision model

**Current candidate: Ultralytics YOLO26 nano/small object-detection checkpoint, after a controlled benchmark.** The official Ultralytics model documentation currently describes YOLO26 as its newest real-time model family and supports object detection. Do not assume a newer model is automatically better for this data: compare YOLO26n with a stable YOLO11n candidate on the same held-out set, hardware and image sizes. Record precision, recall, F1, mAP50, mAP50-95, latency and false-positive examples by class.

Official references:
- YOLO26 model guide: https://docs.ultralytics.com/models/yolo26/
- Ultralytics training guide: https://docs.ultralytics.com/modes/train/
- Ultralytics licensing: https://www.ultralytics.com/license

**Licensing is a project decision, not a footnote.** Ultralytics currently presents AGPL-3.0 and Enterprise licensing options. Its licensing guidance says a proprietary/private application using its code or trained models may require an Enterprise licence unless the project complies with AGPL obligations. Before distributing or deploying CIVIC-I, choose and document the intended licence model. This repository does not grant rights to third-party weights or datasets.

## 2. Candidate training data

### Road damage / potholes

RDD2022 is a candidate source. Its challenge site describes six-country road-image data with bounding-box annotations and four challenge classes, including D40 potholes. It describes the India split as approximately 9,000 training images and 1,000 test images. The published test split is not annotated for local training/evaluation in the ordinary way; use the annotated training data and create a separate local validation/test protocol. Convert only the pothole annotations to CIVIC-I class 0, and inspect the source and image-data licence/terms before redistribution.

Reference: https://crddc2022.sekilab.global/data/

### Garbage accumulation

TACO is a candidate source of contextual litter images with object annotations. It labels individual litter objects across a taxonomy; this is not automatically equivalent to a contiguous garbage-accumulation area. Do not relabel every individual wrapper or bottle as a garbage pile. The initial detector should be trained/evaluated on images labelled consistently for accumulation regions, including locally collected Palghar imagery where consent and collection rights permit.

Reference: https://github.com/pedropro/TACO

### Local evaluation

Public datasets are pretraining/fine-tuning sources, not proof of Palghar performance. Build a geographically and temporally separated Palghar-representative test set. Include monsoon/wet conditions, shadows, varying daylight, road patches, different camera angles, different accumulation patterns and negative examples. Avoid leakage from near-identical video frames or burst photos across train/test splits.

## 3. Spatial database

PostGIS is appropriate for distance and proximity checks. Use `ST_DWithin` with `geography` when the radius is expressed in metres and GiST spatial indexes for relevant spatial columns/expressions. The current prototype also contains a Haversine fallback for SQLite development. Review query plans on real data before production.

References:
- https://postgis.net/docs/ST_DWithin.html
- https://postgis.net/documentation/faq/spatial-indexes/

## 4. Mapping and geocoding

Leaflet is the map renderer; it does not provide map tiles or geocoding by itself. The prototype uses OpenStreetMap's standard raster tile URL for low-volume interactive development and includes visible attribution. OSM Foundation tile servers are community-funded, best-effort services, not an unlimited production tile API. Follow the official policy, honour caching headers, avoid bulk download/prefetch, identify the application and switch to a suitable provider or self-hosted tiles before scale-up.

Public Nominatim is not intended as an unrestricted high-volume geocoder. The prototype therefore supports manual map-pin selection and GPS coordinates instead of depending on address geocoding.

References:
- https://operations.osmfoundation.org/policies/tiles/
- https://operations.osmfoundation.org/policies/nominatim/
- https://leafletjs.com/reference.html

## 5. Indian personal-data rules

The application handles personal data (for example, contact details) and potentially identifying images or location information. Collect the minimum data necessary, provide clear notice, limit access, protect storage and define retention/deletion practices. The Digital Personal Data Protection Rules, 2025 were notified in November 2025 with staggered commencement provisions. Do not assume every provision commenced on the publication date; verify which provisions are in force at the actual launch date and obtain a legal review before public deployment.

Primary source: Gazette of India, G.S.R. 843(E), 13 November 2025:
https://egazette.gov.in/WriteReadData/2025/267647.pdf

## 6. Engineering choices for the current prototype

- Keep exactly two recognition classes: `pothole` and `garbage_accumulation`.
- Keep detection confidence separate from civic priority.
- Use deterministic, transparent priority rules; do not let an LLM invent scores.
- Treat bounding-box area as a coarse visual extent proxy only. It is not a physical pothole-depth, road-safety or waste-mass measurement.
- Unknown factors remain unknown. Do not impute road traffic, duration, recurrence or proximity from assumptions.
- Use human review for classification and consequential status changes.
- Do not claim government integrations, dispatch or work-order creation unless an authorised integration actually exists.
- Display demo data as demo data and unconfigured model status as unconfigured.

## 7. Deployment gates

Before public use, complete at least:

1. Dataset and model licence review.
2. Palghar-specific held-out evaluation for both classes.
3. Verified municipal coverage and road/asset ownership data.
4. Production identity, roles and access review.
5. Distributed rate limiting, abuse monitoring and backup/restore tests.
6. HTTPS, secrets management, storage lifecycle and retention policy.
7. Tile-provider capacity/terms review.
8. Legal/privacy review for applicable DPDP commencement and other relevant requirements.
9. Municipal operating procedure and authorised human reviewers.
10. User testing with residents and officials.
