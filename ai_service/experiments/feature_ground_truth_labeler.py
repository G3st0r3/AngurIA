#!/usr/bin/env python3

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel


ROOT = Path(__file__).resolve().parents[2]

AI_SERVICE = ROOT / "ai_service"

if str(AI_SERVICE) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE))

from intelligence.score_engine_v2 import FEATURES


DATASET = (
    AI_SERVICE
    / "datasets"
    / "watermelon"
)

QUEUE = (
    DATASET
    / "ground_truth"
    / "feature_labeling_queue.csv"
)

OUTPUT = (
    DATASET
    / "ground_truth"
    / "feature_labels_v1.csv"
)

FEATURE_NAMES = [
    "groundSpot",
    "peduncle",
    "stripes",
    "color",
    "surface",
]

EXCLUDED_IDS = {
    "ANG0012",
}

app = FastAPI(
    title="AngurIA Feature Ground Truth Labeler"
)


def load_queue():
    if not QUEUE.exists():
        raise RuntimeError(
            f"Queue not found: {QUEUE}"
        )

    rows = []

    with QUEUE.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        for row in csv.DictReader(handle):
            if row["id"] in EXCLUDED_IDS:
                continue

            rows.append(row)

    return rows


def load_saved():
    if not OUTPUT.exists():
        return {}

    saved = {}

    with OUTPUT.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        for row in csv.DictReader(handle):
            saved[row["id"]] = row

    return saved


def write_saved(saved):
    fields = [
        "id",
        "photo",
        "groundSpot",
        "peduncle",
        "stripes",
        "color",
        "surface",
        "label_source",
        "labeled_at",
    ]

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
        )

        writer.writeheader()

        for key in sorted(saved):
            writer.writerow(saved[key])


class LabelPayload(BaseModel):
    id: str
    groundSpot: str = ""
    peduncle: str = ""
    stripes: str = ""
    color: str = ""
    surface: str = ""


@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(
        """
<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AngurIA Ground Truth Labeler</title>

<style>
body {
    font-family: Arial, sans-serif;
    margin: 0;
    background: #f3f6f3;
    color: #1f2a1f;
}

header {
    background: #1f6f3f;
    color: white;
    padding: 18px 24px;
}

main {
    max-width: 1100px;
    margin: 20px auto;
    padding: 0 16px 30px;
}

.card {
    background: white;
    border-radius: 14px;
    padding: 18px;
    box-shadow: 0 3px 14px rgba(0,0,0,.10);
}

.status {
    margin-bottom: 14px;
    font-weight: bold;
}

.image-wrap {
    text-align: center;
    background: #111;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 18px;
}

img {
    max-width: 100%;
    max-height: 560px;
    object-fit: contain;
}

.grid {
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(180px,1fr));
    gap: 12px;
}

label {
    font-size: 13px;
    font-weight: bold;
}

select {
    width: 100%;
    padding: 10px;
    margin-top: 5px;
}

.buttons {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 18px;
}

button {
    border: 0;
    padding: 11px 16px;
    border-radius: 8px;
    cursor: pointer;
    font-weight: bold;
}

.primary {
    background: #1f6f3f;
    color: white;
}

.secondary {
    background: #dfe7df;
}

.warning {
    background: #f5d06f;
}

.meta {
    margin: 10px 0 16px;
    color: #5f6c5f;
}

.progress {
    margin-bottom: 12px;
    color: #405040;
}
</style>
</head>

<body>

<header>
<h2>🍉 AngurIA — Ground Truth Labeler V1</h2>
</header>

<main>
<div class="card">

<div id="progress" class="progress"></div>
<div id="status" class="status">Caricamento...</div>
<div id="meta" class="meta"></div>

<div class="image-wrap">
<img id="image">
</div>

<div id="fields" class="grid"></div>

<div class="buttons">
<button class="primary" onclick="saveAndNext()">
Salva e prossima
</button>

<button class="secondary" onclick="previous()">
← Precedente
</button>

<button class="secondary" onclick="next()">
Salta →
</button>

<button class="warning" onclick="clearCurrent()">
Non visibile / lascia vuoto
</button>
</div>

</div>
</main>

<script>
let items = [];
let featureValues = {};
let index = 0;

async function init() {
    const response = await fetch('/api/items');
    const data = await response.json();

    items = data.items;
    featureValues = data.feature_values;

    const firstIncomplete =
        items.findIndex(x => !x.completed);

    if (firstIncomplete >= 0) {
        index = firstIncomplete;
    }

    render();
}

function optionHtml(feature, current) {
    const values = featureValues[feature] || [];

    let html =
        '<option value="">-- non visibile / sconosciuto --</option>';

    for (const value of values) {
        const selected =
            value === current ? ' selected' : '';

        html +=
            `<option value="${value}"${selected}>${value}</option>`;
    }

    return html;
}

function render() {
    if (!items.length) {
        document.getElementById('status').innerText =
            'Nessuna immagine disponibile.';
        return;
    }

    const item = items[index];

    document.getElementById('progress').innerText =
        `${index + 1} / ${items.length}`;

    document.getElementById('status').innerText =
        `${item.id} — ${item.completed ? '✅ già etichettata' : 'da etichettare'}`;

    document.getElementById('meta').innerText =
        `Fonte: ${item.source || '-'} | ${item.photo}`;

    document.getElementById('image').src =
        `/image/${item.id}?t=${Date.now()}`;

    const features = [
        'groundSpot',
        'peduncle',
        'stripes',
        'color',
        'surface'
    ];

    const fields =
        document.getElementById('fields');

    fields.innerHTML = '';

    for (const feature of features) {
        const div = document.createElement('div');

        div.innerHTML =
            `<label>${feature}</label>
             <select id="${feature}">
             ${optionHtml(
                 feature,
                 item.labels?.[feature] || ''
             )}
             </select>`;

        fields.appendChild(div);
    }
}

async function saveAndNext() {
    const item = items[index];

    const payload = {
        id: item.id,
        groundSpot:
            document.getElementById('groundSpot').value,
        peduncle:
            document.getElementById('peduncle').value,
        stripes:
            document.getElementById('stripes').value,
        color:
            document.getElementById('color').value,
        surface:
            document.getElementById('surface').value
    };

    const response = await fetch(
        '/api/save',
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        }
    );

    if (!response.ok) {
        alert('Errore salvataggio');
        return;
    }

    items[index].labels = payload;
    items[index].completed = true;

    next();
}

function next() {
    if (index < items.length - 1) {
        index += 1;
    }

    render();
}

function previous() {
    if (index > 0) {
        index -= 1;
    }

    render();
}

function clearCurrent() {
    for (const feature of [
        'groundSpot',
        'peduncle',
        'stripes',
        'color',
        'surface'
    ]) {
        document.getElementById(feature).value = '';
    }
}

init();
</script>

</body>
</html>
"""
    )


@app.get("/api/items")
def items():
    queue = load_queue()
    saved = load_saved()

    response_items = []

    for row in queue:
        saved_row = saved.get(
            row["id"],
            {},
        )

        response_items.append(
            {
                "id": row["id"],
                "photo": row["photo"],
                "source": row["source"],
                "completed":
                    row["id"] in saved,
                "labels": {
                    feature:
                        saved_row.get(feature, "")
                    for feature
                    in FEATURE_NAMES
                },
            }
        )

    feature_values = {
        feature:
            list(
                FEATURES[feature][
                    "mapping"
                ].keys()
            )
        for feature
        in FEATURE_NAMES
    }

    return {
        "items": response_items,
        "feature_values":
            feature_values,
        "excluded":
            sorted(EXCLUDED_IDS),
    }


@app.get("/image/{item_id}")
def image(item_id: str):
    queue = load_queue()

    row = next(
        (
            item
            for item in queue
            if item["id"] == item_id
        ),
        None,
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Unknown item",
        )

    path = ROOT / row["image_path"]

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Image missing",
        )

    return FileResponse(path)


@app.post("/api/save")
def save(payload: LabelPayload):
    queue = load_queue()

    row = next(
        (
            item
            for item in queue
            if item["id"] == payload.id
        ),
        None,
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Unknown item",
        )

    saved = load_saved()

    record = {
        "id": payload.id,
        "photo": row["photo"],
    }

    for feature in FEATURE_NAMES:
        value = getattr(
            payload,
            feature,
        )

        allowed = set(
            FEATURES[feature][
                "mapping"
            ].keys()
        )

        if value and value not in allowed:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid value "
                    f"{feature}={value}"
                ),
            )

        record[feature] = value

    record[
        "label_source"
    ] = "manual_ground_truth"

    record[
        "labeled_at"
    ] = datetime.now().isoformat()

    saved[payload.id] = record

    write_saved(saved)

    return {
        "ok": True,
        "id": payload.id,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8012,
    )
