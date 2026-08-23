import base64
import os
import shutil
import tempfile
import time
import psycopg
from intelligence.real_quality import (
    calculate_prediction_error,
    calculate_real_quality_score,
)
from pathlib import Path
from typing import Optional

import cv2
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO


BASE_DIR = Path(__file__).resolve().parent

DEFAULT_MODEL_PATH = (
    BASE_DIR
    / "runs"
    / "watermelon_v1"
    / "weights"
    / "best.pt"
)

MODEL_PATH = Path(
    os.environ.get(
        "ANGURIA_MODEL_PATH",
        str(DEFAULT_MODEL_PATH),
    )
).expanduser()

MIN_ACCEPTED_CONFIDENCE = 0.25

INFERENCE_IMAGE_SIZE = int(
    os.environ.get(
        "ANGURIA_IMGSZ",
        "640",
    )
)


app = FastAPI(
    title="AngurIA AI Service",
    version="0.3.0",
    description="Servizio locale di rilevamento angurie.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


model: Optional[YOLO] = None
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "",
).strip()


def init_database():
    if not DATABASE_URL:
        print(
            "ℹ️ DATABASE_URL non configurato: "
            "PostgreSQL disattivato"
        )
        return

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS analyses (
                        id TEXT PRIMARY KEY,
                        payload JSONB NOT NULL,
                        status TEXT NOT NULL
                            DEFAULT 'analysis_saved',
                        created_at TIMESTAMPTZ NOT NULL
                            DEFAULT NOW(),
                        updated_at TIMESTAMPTZ NOT NULL
                            DEFAULT NOW()
                    );

                    CREATE TABLE IF NOT EXISTS beta_visits (
                        id BIGSERIAL PRIMARY KEY,
                        beta_friend_id TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL
                            DEFAULT NOW()
                    );

                    CREATE INDEX IF NOT EXISTS
                        idx_beta_visits_beta_friend_id
                    ON beta_visits(beta_friend_id);

                    CREATE INDEX IF NOT EXISTS
                        idx_beta_visits_created_at
                    ON beta_visits(created_at)
                    """
                )

        print(
            "✅ PostgreSQL AngurIA pronto"
        )

    except Exception as error:
        print(
            "⚠️ PostgreSQL non disponibile: "
            f"{error}"
        )

@app.on_event("startup")
def load_model():
    global model

    if not MODEL_PATH.exists():
        raise RuntimeError(
            f"Modello non trovato: {MODEL_PATH}"
        )

    print(f"Caricamento modello: {MODEL_PATH}")

    model = YOLO(str(MODEL_PATH))

    print("✅ Modello AngurIA caricato correttamente")
    init_database()

@app.get("/health")
def health():
    return {
        "service": "AngurIA AI",
        "status": "online",
        "version": "0.3.0",
        "modelLoaded": model is not None,
        "modelPath": str(MODEL_PATH),
        "minimumAcceptedConfidence":
            MIN_ACCEPTED_CONFIDENCE,
        "inferenceImageSize":
            INFERENCE_IMAGE_SIZE,
    }



def estimate_shape_feature(
    image,
    bounding_box,
):
    """
    Stima euristica sperimentale della regolarità
    della forma dell'anguria.

    Restituisce:
    - regular
    - slightly_irregular
    - irregular
    - "" se la stima non è affidabile
    """

    if image is None or not bounding_box:
        return ""

    x = int(bounding_box["x"])
    y = int(bounding_box["y"])
    width = int(bounding_box["width"])
    height = int(bounding_box["height"])

    if width <= 0 or height <= 0:
        return ""

    crop = image[
        max(0, y):max(0, y + height),
        max(0, x):max(0, x + width),
    ]

    if crop.size == 0:
        return ""

    gray = cv2.cvtColor(
        crop,
        cv2.COLOR_BGR2GRAY,
    )

    gray = cv2.GaussianBlur(
        gray,
        (7, 7),
        0,
    )

    edges = cv2.Canny(
        gray,
        40,
        120,
    )

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    if not contours:
        return ""

    contour = max(
        contours,
        key=cv2.contourArea,
    )

    area = cv2.contourArea(contour)

    if area <= 0:
        return ""

    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)

    if hull_area <= 0:
        return ""

    solidity = area / hull_area

    perimeter = cv2.arcLength(
        contour,
        True,
    )

    if perimeter <= 0:
        return ""

    circularity = (
        4.0 * 3.141592653589793 * area
        / (perimeter * perimeter)
    )

    # Se il contorno occupa troppo poco del crop,
    # la stima non è considerata affidabile.
    crop_area = crop.shape[0] * crop.shape[1]

    if crop_area <= 0:
        return ""

    coverage = area / crop_area

    if coverage < 0.20:
        return ""

    if solidity >= 0.94 and circularity >= 0.65:
        return "regular"

    if solidity >= 0.86 and circularity >= 0.45:
        return "slightly_irregular"

    return "irregular"




def estimate_symmetry_feature(
    image,
    bounding_box,
):
    """
    Stima sperimentale della simmetria visiva
    dell'anguria confrontando le due metà
    del contorno principale.

    Restituisce:
    - high
    - medium
    - low
    - "" se la stima non è affidabile
    """

    if image is None or not bounding_box:
        return ""

    x = int(bounding_box["x"])
    y = int(bounding_box["y"])
    width = int(bounding_box["width"])
    height = int(bounding_box["height"])

    if width <= 0 or height <= 0:
        return ""

    crop = image[
        max(0, y):max(0, y + height),
        max(0, x):max(0, x + width),
    ]

    if crop.size == 0:
        return ""

    gray = cv2.cvtColor(
        crop,
        cv2.COLOR_BGR2GRAY,
    )

    gray = cv2.GaussianBlur(
        gray,
        (7, 7),
        0,
    )

    edges = cv2.Canny(
        gray,
        40,
        120,
    )

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    if not contours:
        return ""

    contour = max(
        contours,
        key=cv2.contourArea,
    )

    area = cv2.contourArea(contour)

    crop_area = crop.shape[0] * crop.shape[1]

    if area <= 0 or crop_area <= 0:
        return ""

    coverage = area / crop_area

    if coverage < 0.20:
        return ""

    mask = (
        __import__("numpy").zeros(
            gray.shape,
            dtype="uint8",
        )
    )

    cv2.drawContours(
        mask,
        [contour],
        -1,
        255,
        thickness=-1,
    )

    width_mask = mask.shape[1]

    if width_mask < 4:
        return ""

    middle = width_mask // 2

    left = mask[:, :middle]
    right = mask[:, width_mask - middle:]

    right_flipped = cv2.flip(
        right,
        1,
    )

    intersection = (
        (left > 0) &
        (right_flipped > 0)
    ).sum()

    union = (
        (left > 0) |
        (right_flipped > 0)
    ).sum()

    if union <= 0:
        return ""

    symmetry_ratio = (
        float(intersection)
        / float(union)
    )

    if symmetry_ratio >= 0.90:
        return "high"

    if symmetry_ratio >= 0.75:
        return "medium"

    return "low"



@app.post("/detect")
async def detect_watermelon(
    image: UploadFile = File(...),
):
    print(
        f"📱 DETECT START | "
        f"filename={image.filename} | "
        f"content_type={image.content_type}",
        flush=True,
    )

    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Modello non disponibile",
        )

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    if image.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Formato immagine non supportato",
        )

    suffix = Path(
        image.filename or "image.jpg"
    ).suffix or ".jpg"

    temp_path: Optional[Path] = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:
            shutil.copyfileobj(
                image.file,
                temp_file,
            )

            temp_path = Path(
                temp_file.name
            )

        print(
            f"📥 UPLOAD RICEVUTO | "
            f"path={temp_path} | "
            f"bytes={temp_path.stat().st_size}",
            flush=True,
        )

        started_at = time.perf_counter()

        results = model.predict(
            source=str(temp_path),
            conf=0.01,
            imgsz=INFERENCE_IMAGE_SIZE,
            max_det=20,
            verbose=False,
        )

        inference_time_ms = round(
            (time.perf_counter() - started_at)
            * 1000
        )

        result = results[0]

        candidates = []

        if result.boxes is not None:
            for box in result.boxes:
                class_id = int(box.cls[0])

                confidence = float(
                    box.conf[0]
                )

                x1, y1, x2, y2 = [
                    round(float(value))
                    for value
                    in box.xyxy[0].tolist()
                ]

                candidates.append(
                    {
                        "label":
                            result.names.get(
                                class_id,
                                "watermelon",
                            ),
                        "confidence":
                            round(
                                confidence,
                                4,
                            ),
                        "boundingBox": {
                            "x": x1,
                            "y": y1,
                            "width":
                                max(
                                    0,
                                    x2 - x1,
                                ),
                            "height":
                                max(
                                    0,
                                    y2 - y1,
                                ),
                        },
                    }
                )

        candidates.sort(
            key=lambda candidate:
                candidate["confidence"],
            reverse=True,
        )

        best_candidate = (
            candidates[0]
            if candidates
            else None
        )

        found = (
            best_candidate is not None
            and best_candidate["confidence"]
            >= MIN_ACCEPTED_CONFIDENCE
        )

        annotated_image_base64 = None

        original_image = cv2.imread(
            str(temp_path)
        )

        feature_image = (
            original_image.copy()
            if original_image is not None
            else None
        )

        if (
            original_image is not None
            and best_candidate is not None
        ):
            box = best_candidate[
                "boundingBox"
            ]

            x = int(box["x"])
            y = int(box["y"])
            width = int(box["width"])
            height = int(box["height"])

            x2 = x + width
            y2 = y + height

            if found:
                rectangle_color = (
                    0,
                    180,
                    0,
                )
            else:
                rectangle_color = (
                    0,
                    165,
                    255,
                )

            cv2.rectangle(
                original_image,
                (x, y),
                (x2, y2),
                rectangle_color,
                4,
            )

            confidence_text = (
                f"watermelon "
                f"{best_candidate['confidence'] * 100:.1f}%"
            )

            cv2.putText(
                original_image,
                confidence_text,
                (
                    max(5, x),
                    max(30, y - 10),
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                rectangle_color,
                2,
                cv2.LINE_AA,
            )

            success, encoded_image = (
                cv2.imencode(
                    ".jpg",
                    original_image,
                )
            )

            if success:
                annotated_image_base64 = (
                    base64.b64encode(
                        encoded_image.tobytes()
                    ).decode("utf-8")
                )

        return {
            "found": found,
            "detection": (
                best_candidate
                if found
                else None
            ),
            "bestCandidate":
                best_candidate,
            "rawCandidateCount":
                len(candidates),
            "minimumAcceptedConfidence":
                MIN_ACCEPTED_CONFIDENCE,
            "inferenceTimeMs":
                inference_time_ms,
            "features": {
                "shape": (
                    estimate_shape_feature_grabcut(
                        feature_image,
                        best_candidate["boundingBox"],
                    )
                    if found
                    and best_candidate is not None
                    else ""
                ),
                "symmetry": (
                    estimate_symmetry_feature_grabcut(
                        feature_image,
                        best_candidate["boundingBox"],
                    )
                    if found
                    and best_candidate is not None
                    else ""
                ),
            },
            "annotatedImageBase64":
                annotated_image_base64,
            "image": {
                "filename":
                    image.filename,
                "contentType":
                    image.content_type,
            },
            "warning": (
                "Modello sperimentale "
                "addestrato su dataset minimo."
            ),
        }

    except Exception as error:
        print(
            f"Errore durante inferenza: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    finally:
        await image.close()

        if temp_path is not None:
            temp_path.unlink(
                missing_ok=True
            )

# ============================================================
# ANGURIA SCORE API
# ============================================================

from pydantic import BaseModel
from typing import Optional

from intelligence.score_engine import calculate_anguria_score
from intelligence.score_engine_v2 import calculate_anguria_score as calculate_anguria_score_v2


class ScoreRequest(BaseModel):
    groundSpot: str = ""
    peduncle: str = ""
    shape: str = ""
    stripes: str = ""
    symmetry: str = ""
    color: str = ""
    surface: str = ""


@app.post("/score")
def score_watermelon(payload: ScoreRequest):
    features = {
        "groundSpot": payload.groundSpot,
        "peduncle": payload.peduncle,
        "shape": payload.shape,
        "stripes": payload.stripes,
        "symmetry": payload.symmetry,
        "color": payload.color,
        "surface": payload.surface,
    }

    result = calculate_anguria_score(features)
    shadow_v2 = calculate_anguria_score_v2(features)

    score = result["score"]

    if score >= 80:
        advice = "Acquistala"
    elif score >= 60:
        advice = "Buona candidata"
    elif score >= 40:
        advice = "Valuta con cautela"
    else:
        advice = "Scegline un'altra"

    return {
        "score": score,
        "maxScore": result["maxScore"],
        "advice": advice,
        "recommendation": result["recommendation"],
        "reasons": result["reasons"],
        "warnings": result["warnings"],
        "experimental": result["experimental"],
        "disclaimer": result["disclaimer"],

        "shadowV2": {
            "score": shadow_v2["score"],
            "rawScore": shadow_v2["rawScore"],
            "normalizedScore":
                shadow_v2["normalizedScore"],
            "confidenceAdjustment":
                shadow_v2["confidenceAdjustment"],
            "recoveryFactor":
                shadow_v2["recoveryFactor"],
            "availableMaxScore":
                shadow_v2["availableMaxScore"],
            "completeness":
                shadow_v2["completeness"],
            "observedFeatures":
                shadow_v2["observedFeatures"],
            "missingFeatures":
                shadow_v2["missingFeatures"],
        },
    }


# ============================================================
# ANGURIA BETA VISIT API
# ============================================================

class BetaVisitRequest(BaseModel):
    betaFriendId: str


@app.post("/beta/visit")
def save_beta_visit(payload: BetaVisitRequest):
    beta_friend_id = payload.betaFriendId.strip()

    if not beta_friend_id:
        raise HTTPException(
            status_code=400,
            detail="betaFriendId obbligatorio",
        )

    if not DATABASE_URL:
        return {
            "saved": False,
            "betaFriendId": beta_friend_id,
            "databaseConfigured": False,
        }

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO beta_visits (
                        beta_friend_id
                    )
                    VALUES (%s)
                    """,
                    (beta_friend_id,),
                )

        print(
            f"✅ Beta visit salvata: "
            f"{beta_friend_id}"
        )

        return {
            "saved": True,
            "betaFriendId": beta_friend_id,
        }

    except Exception as error:
        print(
            "⚠️ Salvataggio Beta visit "
            f"non riuscito: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail="Errore salvataggio Beta visit",
        )



# ============================================================
# ANGURIA ANALYSIS SAVE API
# ============================================================

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel


ANALYSIS_HISTORY_DIR = (
    Path(__file__).resolve().parent
    / "datasets"
    / "watermelon"
    / "analysis_history"
)

ANALYSIS_HISTORY_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


class AnalysisSaveRequest(BaseModel):
    score: int
    advice: str
    betaFriendId: str = ""

    groundSpot: str = ""
    peduncle: str = ""
    shape: str = ""
    stripes: str = ""
    symmetry: str = ""
    color: str = ""
    surface: str = ""

    reasons: list = []
    warnings: list = []

    detectorFound: bool = False
    detectorConfidence: float = 0.0
    detectorLabel: str = ""

    shadowV2: dict = {}


@app.post("/analysis/save")
def save_analysis(payload: AnalysisSaveRequest):
    timestamp = datetime.now()

    analysis_id = timestamp.strftime(
        "ANALYSIS_%Y%m%d_%H%M%S_%f"
    )

    data = {
        "id": analysis_id,
        "createdAt": timestamp.isoformat(),

        "score": payload.score,
        "advice": payload.advice,
        "betaFriendId": payload.betaFriendId,

        "features": {
            "groundSpot": payload.groundSpot,
            "peduncle": payload.peduncle,
            "shape": payload.shape,
            "stripes": payload.stripes,
            "symmetry": payload.symmetry,
            "color": payload.color,
            "surface": payload.surface,
        },

        "reasons": payload.reasons,
        "warnings": payload.warnings,

        "detector": {
            "found": payload.detectorFound,
            "confidence": payload.detectorConfidence,
            "label": payload.detectorLabel,
        },

        "shadowV2": payload.shadowV2,

        "status": "saved",
    }

    output_path = (
        ANALYSIS_HISTORY_DIR
        / f"{analysis_id}.json"
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )

    if DATABASE_URL:
        try:
            with psycopg.connect(DATABASE_URL) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO analyses (
                            id,
                            payload,
                            status,
                            created_at,
                            updated_at
                        )
                        VALUES (
                            %s,
                            %s::jsonb,
                            %s,
                            %s,
                            %s
                        )
                        ON CONFLICT (id)
                        DO UPDATE SET
                            payload = EXCLUDED.payload,
                            status = EXCLUDED.status,
                            updated_at = EXCLUDED.updated_at
                        """,
                        (
                            analysis_id,
                            json.dumps(
                                data,
                                ensure_ascii=False,
                            ),
                            data["status"],
                            timestamp,
                            timestamp,
                        ),
                    )

            print(
                f"✅ Analisi PostgreSQL salvata: "
                f"{analysis_id}"
            )

        except Exception as error:
            print(
                "⚠️ Salvataggio PostgreSQL "
                f"non riuscito: {error}"
            )
    return {
        "saved": True,
        "analysisId": analysis_id,
        "path": str(output_path),
    }
# ============================================================
# ANGURIA POST-OPENING FEEDBACK API
# ============================================================

class AnalysisFeedbackRequest(BaseModel):
    sweetness: Optional[int] = None
    crunchiness: Optional[int] = None
    juiciness: Optional[int] = None
    mealiness: Optional[int] = None
    brix: Optional[float] = None
    notes: str = ""


@app.post("/analysis/{analysis_id}/feedback")
def save_analysis_feedback(
    analysis_id: str,
    payload: AnalysisFeedbackRequest,
):
    analysis_path = (
        ANALYSIS_HISTORY_DIR
        / f"{analysis_id}.json"
    )

    if analysis_path.exists():
        with analysis_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    elif DATABASE_URL:
        try:
            with psycopg.connect(DATABASE_URL) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT payload::text
                        FROM analyses
                        WHERE id = %s
                        """,
                        (analysis_id,),
                    )
                    row = cursor.fetchone()

            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="Analisi non trovata",
                )

            data = json.loads(row[0])

            print(
                f"✅ Analisi recuperata da PostgreSQL: "
                f"{analysis_id}"
            )

        except HTTPException:
            raise

        except Exception as error:
            print(
                "⚠️ Lettura PostgreSQL non riuscita: "
                f"{error}"
            )
            raise HTTPException(
                status_code=500,
                detail="Errore recupero analisi",
            )

    else:
        raise HTTPException(
            status_code=404,
            detail="Analisi non trovata",
        )
        data["feedback"] = {
        "sweetness": payload.sweetness,
        "crunchiness": payload.crunchiness,
        "juiciness": payload.juiciness,
        "mealiness": payload.mealiness,
        "brix": payload.brix,
        "notes": payload.notes,
        "updatedAt": datetime.now().isoformat(),
    }
    real_quality_score = calculate_real_quality_score(
    sweetness=payload.sweetness,
    crunchiness=payload.crunchiness,
    juiciness=payload.juiciness,
    mealiness=payload.mealiness,
)

    prediction_error = calculate_prediction_error(
    predicted_score=int(data.get("score", 0)),
    real_score=real_quality_score,
)

    data["realQualityScore"] = real_quality_score
    data["predictionError"] = prediction_error
    data["status"] = "feedback_completed"

    with analysis_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )

    if DATABASE_URL:
        try:
            with psycopg.connect(DATABASE_URL) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE analyses
                        SET
                            payload = %s::jsonb,
                            status = %s,
                            updated_at = NOW()
                        WHERE id = %s
                        """,
                        (
                            json.dumps(
                                data,
                                ensure_ascii=False,
                            ),
                            data["status"],
                            analysis_id,
                        ),
                    )

            print(
                f"✅ Feedback PostgreSQL salvato: "
                f"{analysis_id}"
            )

        except Exception as error:
            print(
                "⚠️ Salvataggio feedback PostgreSQL "
                f"non riuscito: {error}"
            )

    return {
        "saved": True,
        "analysisId": analysis_id,
        "status": "feedback_completed",
    }
def estimate_symmetry_feature_grabcut(
    image,
    bounding_box,
):
    import numpy as np

    if image is None or not bounding_box:
        return ""

    x = max(0, int(bounding_box["x"]))
    y = max(0, int(bounding_box["y"]))
    width = int(bounding_box["width"])
    height = int(bounding_box["height"])

    if width <= 0 or height <= 0:
        return ""

    crop = image[
        y:min(image.shape[0], y + height),
        x:min(image.shape[1], x + width),
    ]

    if crop.size == 0:
        return ""

    crop_height, crop_width = crop.shape[:2]

    if crop_width < 20 or crop_height < 20:
        return ""

    mask = np.full(
        (crop_height, crop_width),
        cv2.GC_PR_BGD,
        dtype=np.uint8,
    )

    border_x = max(2, int(crop_width * 0.04))
    border_y = max(2, int(crop_height * 0.04))

    mask[
        border_y:crop_height - border_y,
        border_x:crop_width - border_x,
    ] = cv2.GC_PR_FGD

    mask[
        int(crop_height * 0.25):int(crop_height * 0.75),
        int(crop_width * 0.25):int(crop_width * 0.75),
    ] = cv2.GC_FGD

    bg_model = np.zeros((1, 65), np.float64)
    fg_model = np.zeros((1, 65), np.float64)

    cv2.setRNGSeed(42)

    cv2.grabCut(
        crop,
        mask,
        None,
        bg_model,
        fg_model,
        5,
        cv2.GC_INIT_WITH_MASK,
    )

    binary = np.where(
        (mask == cv2.GC_FGD)
        | (mask == cv2.GC_PR_FGD),
        255,
        0,
    ).astype("uint8")

    contours, _ = cv2.findContours(
        binary,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    if not contours:
        return ""

    contour = max(
        contours,
        key=cv2.contourArea,
    )

    area = cv2.contourArea(contour)
    crop_area = crop_height * crop_width

    if area <= 0 or crop_area <= 0:
        return ""

    coverage = area / float(crop_area)

    if coverage < 0.20:
        return ""

    object_mask = np.zeros_like(binary)

    cv2.drawContours(
        object_mask,
        [contour],
        -1,
        255,
        -1,
    )

    middle = crop_width // 2

    if middle <= 1:
        return ""

    left = object_mask[:, :middle]
    right = object_mask[:, crop_width - middle:]
    right = cv2.flip(right, 1)

    intersection = (
        (left > 0)
        & (right > 0)
    ).sum()

    union = (
        (left > 0)
        | (right > 0)
    ).sum()

    if union <= 0:
        return ""

    symmetry_ratio = (
        float(intersection)
        / float(union)
    )

    if symmetry_ratio >= 0.90:
        return "high"

    if symmetry_ratio >= 0.75:
        return "medium"

    return "low"

def estimate_shape_feature_grabcut(
    image,
    bounding_box,
):
    import numpy as np

    if image is None or not bounding_box:
        return ""

    x = max(0, int(bounding_box["x"]))
    y = max(0, int(bounding_box["y"]))
    width = int(bounding_box["width"])
    height = int(bounding_box["height"])

    if width <= 0 or height <= 0:
        return ""

    crop = image[
        y:min(image.shape[0], y + height),
        x:min(image.shape[1], x + width),
    ]

    if crop.size == 0:
        return ""

    h, w = crop.shape[:2]

    if w < 20 or h < 20:
        return ""

    mask = np.full(
        (h, w),
        cv2.GC_PR_BGD,
        dtype=np.uint8,
    )

    bx = max(2, int(w * 0.04))
    by = max(2, int(h * 0.04))

    mask[
        by:h - by,
        bx:w - bx,
    ] = cv2.GC_PR_FGD

    mask[
        int(h * 0.25):int(h * 0.75),
        int(w * 0.25):int(w * 0.75),
    ] = cv2.GC_FGD

    bg_model = np.zeros((1, 65), np.float64)
    fg_model = np.zeros((1, 65), np.float64)

    cv2.setRNGSeed(42)

    cv2.grabCut(
        crop,
        mask,
        None,
        bg_model,
        fg_model,
        5,
        cv2.GC_INIT_WITH_MASK,
    )

    binary = np.where(
        (mask == cv2.GC_FGD)
        | (mask == cv2.GC_PR_FGD),
        255,
        0,
    ).astype("uint8")

    contours, _ = cv2.findContours(
        binary,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    if not contours:
        return ""

    contour = max(
        contours,
        key=cv2.contourArea,
    )

    area = cv2.contourArea(contour)

    if area <= 0:
        return ""

    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)

    if hull_area <= 0:
        return ""

    solidity = area / hull_area

    perimeter = cv2.arcLength(
        contour,
        True,
    )

    if perimeter <= 0:
        return ""

    circularity = (
        4.0 * 3.141592653589793 * area
        / (perimeter * perimeter)
    )

    coverage = area / float(h * w)

    if coverage < 0.20:
        return ""

    if solidity >= 0.94 and circularity >= 0.65:
        return "regular"

    if solidity >= 0.86 and circularity >= 0.45:
        return "slightly_irregular"

    return "irregular"
