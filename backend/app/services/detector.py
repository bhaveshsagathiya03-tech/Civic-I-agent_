"""Real YOLO integration. No mock or fabricated detections are produced."""
from pathlib import Path
from threading import Lock
from typing import Any
from ..core.config import settings

class DetectorUnavailable(RuntimeError):
    pass

class YoloDetector:
    def __init__(self):
        self._model = None
        self._lock = Lock()
        self._error: str | None = None
        self._weights = settings.yolo_weights

    @property
    def status(self) -> dict[str, Any]:
        if not self._weights:
            return {"state": "not_configured", "message": "Set YOLO_WEIGHTS to a validated two-class model checkpoint.", "weights": None}
        if not Path(self._weights).is_file():
            return {"state": "weights_missing", "message": "Configured YOLO weights file was not found.", "weights": self._weights}
        if self._model is None and self._error is None:
            return {"state": "configured_not_loaded", "message": "Weights are configured; model loads on first inference.", "weights": self._weights}
        if self._error:
            return {"state": "load_error", "message": self._error, "weights": self._weights}
        return {"state": "ready", "message": "Model loaded.", "weights": self._weights}

    def _load(self):
        if self._model is not None:
            return
        if not self._weights or not Path(self._weights).is_file():
            raise DetectorUnavailable("YOLO model is not configured. No prediction was generated.")
        try:
            from ultralytics import YOLO
            model = YOLO(self._weights)
            names = model.names
            names_map = {int(k): str(v).strip().lower() for k, v in names.items()} if isinstance(names, dict) else {i: str(v).strip().lower() for i, v in enumerate(names)}
            required = {"pothole", "garbage_accumulation"}
            if set(names_map.values()) != required or len(names_map) != 2:
                raise DetectorUnavailable(f"Weights must contain exactly the supported target classes or at minimum {sorted(required)}. Found: {names_map}")
            self._model = model
        except DetectorUnavailable:
            raise
        except Exception as exc:
            self._error = str(exc)
            raise DetectorUnavailable(f"Unable to load YOLO weights: {exc}") from exc

    def predict(self, image_path: str) -> dict[str, Any]:
        with self._lock:
            self._load()
            results = self._model.predict(source=image_path, conf=settings.yolo_confidence, verbose=False)
        names = self._model.names
        names_map = {int(k): str(v).strip().lower() for k, v in names.items()} if isinstance(names, dict) else {i: str(v).strip().lower() for i, v in enumerate(names)}
        boxes_out = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                cls_id = int(box.cls.item())
                label = names_map.get(cls_id, "unknown")
                if label not in {"pothole", "garbage_accumulation"}:
                    continue
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
                boxes_out.append({"category": label, "confidence": float(box.conf.item()), "bbox_xyxy": [x1, y1, x2, y2]})
        primary = max(boxes_out, key=lambda x: x["confidence"], default=None)
        annotated_path = None
        if results and getattr(results[0], "save", None):
            # Render to a deterministic app-owned location without depending on Ultralytics' project folders.
            import cv2
            from PIL import Image
            img = cv2.imread(image_path)
            if img is not None:
                for det in boxes_out:
                    x1, y1, x2, y2 = [int(v) for v in det["bbox_xyxy"]]
                    cv2.rectangle(img, (x1, y1), (x2, y2), (20, 155, 120), 2)
                    cv2.putText(img, f"{det['category']} {det['confidence']:.2f}", (x1, max(18, y1-7)), cv2.FONT_HERSHEY_SIMPLEX, .55, (20,155,120), 2)
                annotated_path = image_path.rsplit(".", 1)[0] + "_annotated.jpg"
                cv2.imwrite(annotated_path, img)
        return {"state": "completed", "detections": boxes_out, "primary_category": primary["category"] if primary else None, "primary_confidence": primary["confidence"] if primary else None, "annotated_path": annotated_path, "model": settings.model_name}

detector = YoloDetector()
