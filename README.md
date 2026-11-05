# CIVIC-I — Civic Eye AI

CIVIC-I is a civic issue reporting and intelligence prototype for Palghar City. Its MVP supports **exactly two computer-vision categories**:

1. `pothole`
2. `garbage_accumulation`

Citizens can submit an image and location. The API validates and stores the report, runs a configured two-class YOLO checkpoint when available, checks for nearby reports, and calculates a transparent provisional priority score from available evidence. An admin can review reports, update workflow status, and view reports on a map.

> **Model honesty:** The repository does not contain trained CIVIC-I weights or Palghar-labelled training data. By default, YOLO is not configured. In that state, the application still accepts and stores citizen reports but explicitly marks AI analysis unavailable and does not invent detections or priority scores. This is intentional.

## Current implementation status

- FastAPI backend, SQLAlchemy persistence, upload validation/re-encoding, JWT admin login, issue tracking, basic analytics and audit history: implemented in source.
- SQLite is the local default so the prototype can be started without installing PostgreSQL. PostgreSQL/PostGIS is supported by configuration; duplicate-distance queries use `ST_DWithin` when PostGIS is available and fall back to Haversine distance otherwise.
- React/Vite citizen and admin interfaces: source included. Frontend dependency installation/build was not verified in this environment because npm registry access timed out.
- YOLO integration: real inference adapter included, but requires `YOLO_WEIGHTS` to point to a compatible model with class names `pothole` and `garbage_accumulation`. No trained checkpoint is included.
- Training/evaluation scripts: included. Actual model accuracy is not claimed.
- Municipal integration: not included; no official API credentials or municipal partnership was provided.

## Architecture

```text
Citizen PWA / Admin Console (React + Vite)
                |
                v
          FastAPI REST API
                |
        Report validation & storage
                |
        YOLO detector (optional until weights exist)
                |
      Duplicate candidate search
                |
      Explainable priority engine
                |
    PostgreSQL/PostGIS or SQLite
                |
        Admin review & tracking
```

## Requirements

- Python 3.11 or newer (Python 3.13 was used for source-level checks here).
- Node.js 20 or newer and npm for the React frontend.
- SQLite for local quick-start, or PostgreSQL with PostGIS for a GIS-backed deployment.
- Optional: PyTorch/Ultralytics and compatible trained YOLO weights for automated image detection.

## Quick start — local development

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows; on macOS/Linux use: cp .env.example .env
```

Edit `backend/.env` and set a strong `SECRET_KEY`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD`. Do not reuse the example placeholder values. Keep the file private.

Run the API from the `backend` directory:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs: http://127.0.0.1:8000/docs
Health: http://127.0.0.1:8000/health

The admin account is created on startup only when both `ADMIN_EMAIL` and `ADMIN_PASSWORD` are set. Anonymous citizen report submission is enabled for the prototype; production deployment should add rate limiting, abuse controls and a reviewed identity/anonymous-report policy.

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

The frontend expects the API at `http://localhost:8000` by default. To override it, create `frontend/.env.local` with:

```dotenv
VITE_API_BASE=http://localhost:8000
```

### 3. Enable real YOLO inference

Install the optional ML dependencies:

```bash
cd backend
pip install -r requirements-ml.txt
```

Place a trained CIVIC-I two-class checkpoint at a protected local path and set in `backend/.env`:

```dotenv
YOLO_WEIGHTS=./models/civic_i_best.pt
YOLO_CONFIDENCE=0.35
```

The checkpoint must have the exact class mapping:

```text
0 = pothole
1 = garbage_accumulation
```

Restart the backend. The `/api/v1/models/status` endpoint (admin-authenticated) and the dashboard model health page show whether the checkpoint is ready. A generic COCO model is not sufficient.

## Admin sign-in

Use the email/password configured in `backend/.env`:

```dotenv
ADMIN_EMAIL=your-admin-email
ADMIN_PASSWORD=your-strong-password
```

No default production credentials are included. The example credentials must be changed.

## API overview

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| POST | `/api/v1/issues` | Public prototype submission | Upload image and location |
| GET | `/api/v1/issues/track/{public_id}` | Public | Track non-sensitive status |
| POST | `/api/v1/auth/login` | Public | Obtain admin JWT |
| GET | `/api/v1/auth/me` | Authenticated | Current user |
| GET | `/api/v1/issues` | Admin/reviewer | List and filter issues |
| GET | `/api/v1/issues/{id}` | Admin/reviewer | Issue detail and history |
| PATCH | `/api/v1/issues/{id}/review` | Admin/reviewer | Update status / category verification / priority override |
| PATCH | `/api/v1/issues/{id}/priority-context` | Admin/reviewer | Recalculate priority from reviewer-entered context |
| POST | `/api/v1/issues/{id}/resolution-evidence` | Admin/reviewer | Upload completion evidence; moves issue to work-reported-completed |
| GET | `/api/v1/issues/{id}/evidence/{kind}` | Admin/reviewer | Retrieve protected original, annotated or resolution image |
| GET | `/api/v1/map/issues` | Admin/reviewer | Map data |
| GET | `/api/v1/analytics/overview` | Admin/reviewer | Dashboard counters |
| GET | `/api/v1/models/status` | Admin/reviewer | YOLO readiness |

## Dataset preparation and training

See [`docs/DATA_AND_MODEL.md`](docs/DATA_AND_MODEL.md), [`docs/RESEARCH_AND_DECISIONS.md`](docs/RESEARCH_AND_DECISIONS.md) and [`backend/training/README.md`](backend/training/README.md). The research note records current model, dataset, map-service, licensing and privacy decisions with source links.

The expected dataset format is YOLO object detection with the two class IDs. RDD2022 is a candidate source for potholes. TACO is a candidate litter-context dataset, but isolated litter labels must not be incorrectly relabelled as garbage-accumulation zones. Locally labelled accumulation-region images are needed.

Example:

```bash
cd backend/training
cp data.yaml.example data.yaml
python validate_dataset.py --data data.yaml
python train.py --data data.yaml --model yolo26n.pt --epochs 100 --imgsz 640 --batch 8 --device cpu
python evaluate.py --weights runs/detect/civic_i_two_class/weights/best.pt --data data.yaml --split test
```

Training on CPU can take a long time. A CUDA-capable GPU or an appropriately governed cloud training environment is recommended. Check the model/software and dataset licences before redistribution or deployment.

## Docker deployment

The repository includes a Docker Compose setup for PostgreSQL/PostGIS, API and frontend. Configure secrets in a root `.env` file before starting it:

```bash
cp .env.docker.example .env
docker compose up --build
```

This configuration is a deployment starting point, not a security-reviewed production environment. Configure HTTPS, backups, firewall policy, secrets, storage lifecycle, monitoring, rate limiting and access controls before public use.

## Important limitations

1. No validated two-class weights are shipped.
2. No Palghar municipal boundary or authoritative road-ownership dataset is shipped. The map's default view is only an approximate city centre.
3. The current priority score uses only factors for which values exist. A score derived from visual bounding-box area is explicitly provisional and is not a road-safety engineering assessment.
4. Automatic official complaint filing, work orders and municipal dispatch are not implemented.
5. Public issue tracking uses an unguessable reference ID but is not a substitute for a production privacy/security review.
6. The frontend has not been installed or built in this network-restricted environment; run `npm install` and `npm run build` locally to verify it.
7. Ultralytics licensing must be reviewed for the intended distribution/deployment model. AGPL-3.0 and Enterprise options have different obligations.

## Tests

```bash
cd backend
pytest -q
```

For frontend type-check/build:

```bash
cd frontend
npm install
npm run build
```

## Project structure

```text
civic-i/
  backend/
    app/
      api/          # FastAPI routes
      core/         # Settings and security
      models/       # SQLAlchemy entities
      services/     # YOLO, media, duplicates, priority
    tests/
    training/       # Dataset validation, training, evaluation
  frontend/
    src/            # Citizen UI, admin console, map, components
  docs/             # Data/model and technical notes
  docker-compose.yml
  README.md
```
