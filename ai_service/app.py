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
                    )
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
    }


@app.post("/detect")
async def detect_watermelon(
    image: UploadFile = File(...),
):
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

        started_at = time.perf_counter()

        results = model.predict(
            source=str(temp_path),
            conf=0.01,
            imgsz=640,
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
    }


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