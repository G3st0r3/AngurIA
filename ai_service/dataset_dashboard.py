import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse


BASE_DIR = Path(__file__).resolve().parent

DATASET_DIR = BASE_DIR / "datasets" / "watermelon"

RAW_OWN_DIR = DATASET_DIR / "raw" / "own"
CARDS_DIR = DATASET_DIR / "cards"
ANNOTATIONS_DIR = DATASET_DIR / "annotations"

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


app = FastAPI(
    title="AngurIA Dataset Explorer",
    version="0.2.0",
)


def get_images():
    if not RAW_OWN_DIR.exists():
        return []

    return sorted(
        file
        for file in RAW_OWN_DIR.iterdir()
        if file.is_file()
        and file.suffix.lower() in IMAGE_EXTENSIONS
    )


def load_cards():
    if not CARDS_DIR.exists():
        return {}

    cards = {}

    for file in sorted(CARDS_DIR.glob("ANG*.json")):
        try:
            with file.open(
                "r",
                encoding="utf-8",
            ) as handle:
                card = json.load(handle)

            item_id = card.get("id")

            if item_id:
                cards[item_id] = card

        except Exception as error:
            print(
                f"Errore caricamento {file.name}: {error}"
            )

    return cards


def get_annotated_ids():
    if not ANNOTATIONS_DIR.exists():
        return set()

    return {
        file.stem
        for file in ANNOTATIONS_DIR.glob("*.txt")
        if file.is_file()
    }


@app.get(
    "/image/{filename}",
    response_class=FileResponse,
)
def get_image(filename: str):
    safe_filename = Path(filename).name

    image_path = RAW_OWN_DIR / safe_filename

    if not image_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Immagine non trovata",
        )

    return FileResponse(image_path)


@app.get(
    "/annotate/{item_id}",
    response_class=HTMLResponse,
)
def annotate_image(item_id: str):

    card_path = CARDS_DIR / f"{item_id}.json"

    if not card_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Scheda non trovata",
        )

    with card_path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        card = json.load(handle)

    filename = Path(
        card.get("photo", "")
    ).name

    image_path = RAW_OWN_DIR / filename

    if not image_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Immagine non trovata",
        )

    html = """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta
            name="viewport"
            content="width=device-width, initial-scale=1"
        >
        <title>Annotazione __ITEM_ID__</title>

        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont,
                    "Segoe UI", Arial, sans-serif;
                background: #f4f8f3;
                margin: 0;
                color: #243124;
            }

            .container {
                max-width: 1000px;
                margin: auto;
                padding: 24px;
            }

            h1 {
                color: #2e7d32;
            }

            .stage {
                position: relative;
                display: inline-block;
                max-width: 100%;
                background: #111;
                line-height: 0;
                user-select: none;
            }

            #photo {
                display: block;
                max-width: 100%;
                max-height: 70vh;
            }

            #canvas {
                position: absolute;
                left: 0;
                top: 0;
                cursor: crosshair;
            }

            button {
                margin-top: 20px;
                padding: 12px 20px;
                border: 0;
                border-radius: 12px;
                background: #2e7d32;
                color: white;
                font-size: 16px;
                font-weight: 700;
                cursor: pointer;
            }

            #status {
                margin-top: 15px;
                font-weight: 700;
            }
        </style>
    </head>

    <body>
        <div class="container">
            <a href="/card/__ITEM_ID__">
                ← Torna alla scheda
            </a>

            <h1>🍉 Annotazione __ITEM_ID__</h1>

            <p>
                Trascina il mouse attorno all'anguria.
                Il rettangolo deve seguire il bordo
                il più possibile.
            </p>

            <div class="stage">
                <img
                    id="photo"
                    src="/image/__FILENAME__"
                    alt="__ITEM_ID__"
                >
                <canvas id="canvas"></canvas>
            </div>

            <br>

            <button id="save">
                Salva bounding box
            </button>

            <div id="status"></div>
        </div>

        <script>
            const img = document.getElementById("photo");
            const canvas = document.getElementById("canvas");
            const ctx = canvas.getContext("2d");
            const status = document.getElementById("status");

            let startX = 0;
            let startY = 0;
            let currentBox = null;
            let drawing = false;

            function resizeCanvas() {
                canvas.width = img.clientWidth;
                canvas.height = img.clientHeight;
                canvas.style.width = img.clientWidth + "px";
                canvas.style.height = img.clientHeight + "px";
                redraw();
            }

            function redraw() {
                ctx.clearRect(
                    0,
                    0,
                    canvas.width,
                    canvas.height
                );

                if (!currentBox) {
                    return;
                }

                ctx.strokeStyle = "#ff2d2d";
                ctx.lineWidth = 4;

                ctx.strokeRect(
                    currentBox.x,
                    currentBox.y,
                    currentBox.width,
                    currentBox.height
                );
            }

            function pointerPosition(event) {
                const rect =
                    canvas.getBoundingClientRect();

                return {
                    x: event.clientX - rect.left,
                    y: event.clientY - rect.top
                };
            }

            canvas.addEventListener(
                "mousedown",
                function(event) {
                    const p = pointerPosition(event);

                    startX = p.x;
                    startY = p.y;
                    drawing = true;
                    currentBox = null;
                }
            );

            canvas.addEventListener(
                "mousemove",
                function(event) {
                    if (!drawing) {
                        return;
                    }

                    const p = pointerPosition(event);

                    currentBox = {
                        x: Math.min(startX, p.x),
                        y: Math.min(startY, p.y),
                        width: Math.abs(p.x - startX),
                        height: Math.abs(p.y - startY)
                    };

                    redraw();
                }
            );

            window.addEventListener(
                "mouseup",
                function() {
                    drawing = false;
                }
            );

            const saveButton =
                document.getElementById("save");

            saveButton.addEventListener(
                "click",
                async function() {
                    saveButton.disabled = true;
                    saveButton.textContent =
                        "Salvataggio...";

                        if (
                            !currentBox ||
                            currentBox.width < 5 ||
                            currentBox.height < 5
                        ) {
                            status.textContent =
                                "⚠️ Disegna prima il rettangolo.";
                            return;
                        }

                        const payload = {
                            x:
                                currentBox.x /
                                canvas.width,
                            y:
                                currentBox.y /
                                canvas.height,
                            width:
                                currentBox.width /
                                canvas.width,
                            height:
                                currentBox.height /
                                canvas.height
                        };

                        const response = await fetch(
                            "/annotate/__ITEM_ID__",
                            {
                                method: "POST",
                                headers: {
                                    "Content-Type":
                                        "application/json"
                                },
                                body:
                                    JSON.stringify(payload)
                            }
                        );

                        const result =
                            await response.json();

                        if (response.ok) {
                            saveButton.textContent =
                                "✅ Salvato";

                            if (result.nextItemId) {
                                status.textContent =
                                    "✅ Salvata. Passo alla prossima...";

                                setTimeout(
                                    function() {
                                        window.location.href =
                                            "/annotate/" +
                                            result.nextItemId;
                                    },
                                    600
                                );
                            } else {
                                status.textContent =
                                    "✅ Annotazione salvata. "
                                    + "Nessun'altra immagine da annotare.";
                            }
                        } else {
                            saveButton.disabled = false;
                            saveButton.textContent =
                                "Salva bounding box";

                            status.textContent =
                                "❌ " +
                                (
                                    result.detail ||
                                    "Errore salvataggio"
                                );
                        }
                    }
                );

            img.addEventListener(
                "load",
                resizeCanvas
            );

            window.addEventListener(
                "resize",
                resizeCanvas
            );
        </script>
    </body>
    </html>
    """

    return html.replace(
        "__ITEM_ID__",
        item_id,
    ).replace(
        "__FILENAME__",
        filename,
    )


@app.post("/annotate/{item_id}")
async def save_web_annotation(
    item_id: str,
    request: Request,
):
    card_path = CARDS_DIR / f"{item_id}.json"

    if not card_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Scheda non trovata",
        )

    payload = await request.json()

    try:
        x = float(payload["x"])
        y = float(payload["y"])
        width = float(payload["width"])
        height = float(payload["height"])
    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        raise HTTPException(
            status_code=400,
            detail="Bounding box non valida",
        )

    if (
        x < 0 or
        y < 0 or
        width <= 0 or
        height <= 0 or
        x + width > 1.001 or
        y + height > 1.001
    ):
        raise HTTPException(
            status_code=400,
            detail="Bounding box fuori immagine",
        )

    center_x = x + width / 2
    center_y = y + height / 2

    ANNOTATIONS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    label_path = (
        ANNOTATIONS_DIR /
        f"{item_id}.txt"
    )

    label_path.write_text(
        (
            f"0 "
            f"{center_x:.6f} "
            f"{center_y:.6f} "
            f"{width:.6f} "
            f"{height:.6f}\n"
        ),
        encoding="utf-8",
    )

    with card_path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        card = json.load(handle)

    card["trainingStatus"] = "annotated"

    with card_path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            card,
            handle,
            ensure_ascii=False,
            indent=2,
        )

    annotated_ids = get_annotated_ids()

    next_item_id = None

    for image in get_images():
        candidate_id = image.stem

        if candidate_id not in annotated_ids:
            next_item_id = candidate_id
            break

    return {
        "ok": True,
        "itemId": item_id,
        "label":
            label_path.name,
        "nextItemId":
            next_item_id,
    }



@app.get("/", response_class=HTMLResponse)
def dashboard():
    images = get_images()
    cards = load_cards()
    annotated_ids = get_annotated_ids()

    total_images = len(images)
    total_cards = len(cards)
    total_annotations = len(annotated_ids)

    gallery_items = []

    for image in images:
        item_id = image.stem

        card = cards.get(
            item_id,
            {},
        )

        is_annotated = (
            item_id in annotated_ids
        )

        status_text = (
            "Annotata"
            if is_annotated
            else "Da annotare"
        )

        status_class = (
            "done"
            if is_annotated
            else "todo"
        )

        variety = (
            card.get("variety")
            or "Non indicata"
        )

        source = (
            card.get("source")
            or "Non indicata"
        )

        date = (
            card.get("date")
            or "-"
        )

        score = card.get("anguriaScore")

        score_html = (
            f'<div class="score-badge">{score}/100</div>'
            if score is not None
            else '<div class="score-badge empty-score">--</div>'
        )

        gallery_items.append(
            f"""
            <a
                class="card-link"
                href="/card/{item_id}"
            >
                <div class="watermelon-card">

                    <div class="image-wrapper">

                        <img
                            src="/image/{image.name}"
                            alt="{item_id}"
                        >

                        <div class="badge {status_class}">
                            {status_text}
                        </div>

                        {score_html}

                    </div>

                    <div class="info">

                        <div class="id">
                            {item_id}
                        </div>

                        <div class="filename">
                            {image.name}
                        </div>

                        <div class="details">
                            <span>
                                Varietà:
                                <strong>
                                    {variety}
                                </strong>
                            </span>

                            <span>
                                Fonte:
                                <strong>
                                    {source}
                                </strong>
                            </span>

                            <span>
                                Data:
                                <strong>
                                    {date}
                                </strong>
                            </span>
                        </div>

                    </div>

                </div>
            </a>
            """
        )

    gallery_html = "\n".join(
        gallery_items
    )

    next_unannotated_id = next(
        (
            image.stem
            for image in images
            if image.stem not in annotated_ids
        ),
        None,
    )

    if next_unannotated_id:
        annotation_action_html = f"""
        <div style="margin: 22px 0;">
            <a
                href="/annotate/{next_unannotated_id}"
                style="
                    display: inline-block;
                    background: #2e7d32;
                    color: white;
                    text-decoration: none;
                    font-weight: 800;
                    padding: 13px 20px;
                    border-radius: 12px;
                "
            >
                🍉 Annota prossima
            </a>
        </div>
        """
    else:
        annotation_action_html = """
        <div style="
            margin: 22px 0;
            font-weight: 700;
            color: #2e7d32;
        ">
            ✅ Tutte le immagini sono annotate
        </div>
        """

    if not gallery_html:
        gallery_html = """
        <div class="empty">
            Nessuna immagine presente nel dataset.
        </div>
        """

    html = f"""
    <!DOCTYPE html>

    <html lang="it">

    <head>

        <meta charset="UTF-8">

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1"
        >

        <title>
            AngurIA Dataset Explorer
        </title>

        <style>

            * {{
                box-sizing: border-box;
            }}

            body {{
                font-family:
                    -apple-system,
                    BlinkMacSystemFont,
                    "Segoe UI",
                    Arial,
                    sans-serif;

                background: #f4f8f3;

                margin: 0;

                color: #243124;
            }}

            .header {{
                background: white;

                padding: 28px 32px;

                border-bottom:
                    1px solid #dfe8df;
            }}

            h1 {{
                margin: 0;

                color: #2e7d32;

                font-size: 32px;
            }}

            .subtitle {{
                margin-top: 7px;

                color: #6b796b;
            }}

            .container {{
                max-width: 1400px;

                margin: auto;

                padding: 28px;
            }}

            .stats {{
                display: grid;

                grid-template-columns:
                    repeat(
                        auto-fit,
                        minmax(180px, 1fr)
                    );

                gap: 16px;

                margin-bottom: 30px;
            }}

            .stat-card {{
                background: white;

                padding: 22px;

                border-radius: 18px;

                box-shadow:
                    0 5px 20px
                    rgba(0, 0, 0, 0.05);
            }}

            .stat-number {{
                font-size: 38px;

                font-weight: 800;

                color: #2e7d32;
            }}

            .stat-label {{
                margin-top: 6px;

                color: #687668;
            }}

            .section-title {{
                margin:
                    10px 0 18px;

                font-size: 22px;
            }}

            .gallery {{
                display: grid;

                grid-template-columns:
                    repeat(
                        auto-fill,
                        minmax(260px, 1fr)
                    );

                gap: 20px;
            }}

            .card-link {{
                text-decoration: none;
                color: inherit;
            }}

            .score-badge {{
                position: absolute;
                left: 12px;
                bottom: 12px;
                padding: 8px 12px;
                border-radius: 30px;
                background: #2e7d32;
                color: white;
                font-weight: 800;
                font-size: 14px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.18);
            }}

            .score-badge.empty-score {{
                background: #7a877a;
            }}

            .watermelon-card {{
                background: white;

                border-radius: 20px;

                overflow: hidden;

                box-shadow:
                    0 6px 22px
                    rgba(0, 0, 0, 0.07);
            }}

            .image-wrapper {{
                position: relative;

                height: 220px;

                background: #e7eee7;
            }}

            .image-wrapper img {{
                width: 100%;

                height: 100%;

                object-fit: cover;
            }}

            .badge {{
                position: absolute;

                top: 12px;

                right: 12px;

                padding:
                    7px 11px;

                border-radius: 30px;

                font-size: 12px;

                font-weight: 700;

                color: white;
            }}

            .badge.done {{
                background: #2e7d32;
            }}

            .badge.todo {{
                background: #ef8f00;
            }}

            .info {{
                padding: 17px;
            }}

            .id {{
                font-size: 21px;

                font-weight: 800;

                color: #2e7d32;
            }}

            .filename {{
                margin-top: 3px;

                color: #7a877a;

                font-size: 13px;
            }}

            .details {{
                display: flex;

                flex-direction: column;

                gap: 6px;

                margin-top: 14px;

                font-size: 14px;
            }}

            .empty {{
                background: white;

                padding: 50px;

                border-radius: 18px;

                text-align: center;

                color: #687668;
            }}

        </style>

    </head>

    <body>

        <div class="header">

            <h1>
                🍉 AngurIA Dataset Explorer
            </h1>

            <div class="subtitle">
                Dataset proprietario e stato
                delle annotazioni
            </div>

        </div>

        <div class="container">

            <div class="stats">

                <div class="stat-card">

                    <div class="stat-number">
                        {total_images}
                    </div>

                    <div class="stat-label">
                        Immagini
                    </div>

                </div>

                <div class="stat-card">

                    <div class="stat-number">
                        {total_cards}
                    </div>

                    <div class="stat-label">
                        Schede JSON
                    </div>

                </div>

                <div class="stat-card">

                    <div class="stat-number">
                        {total_annotations}
                    </div>

                    <div class="stat-label">
                        Annotate
                    </div>

                </div>

                <div class="stat-card">

                    <div class="stat-number">
                        {max(
                            0,
                            total_images
                            - total_annotations,
                        )}
                    </div>

                    <div class="stat-label">
                        Da annotare
                    </div>

                </div>

            </div>

            {annotation_action_html}

            <h2 class="section-title">
                Galleria Dataset
            </h2>

            <div class="gallery">
                {gallery_html}
            </div>

        </div>

    </body>

    </html>
    """

    return HTMLResponse(
        content=html
    )

# ============================================================
# ANGURIA CARD EDITOR
# ============================================================

from fastapi import Form
from fastapi.responses import RedirectResponse

from intelligence.score_engine import calculate_anguria_score


@app.get("/card/{item_id}", response_class=HTMLResponse)
def card_editor(item_id: str):
    card_path = CARDS_DIR / f"{item_id}.json"

    if not card_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Scheda non trovata",
        )

    with card_path.open("r", encoding="utf-8") as file:
        card = json.load(file)

    def selected(field, value):
        return (
            "selected"
            if card.get(field, "") == value
            else ""
        )

    current_score = card.get("anguriaScore")

    if current_score is None:
        score_text = "Non ancora calcolato"
        advice_text = "Completa la valutazione"
        advice_class = "neutral"

    else:
        score_text = f"{current_score}/100"

        if current_score >= 80:
            advice_text = "Acquistala"
            advice_class = "excellent"

        elif current_score >= 60:
            advice_text = "Buona candidata"
            advice_class = "good"

        elif current_score >= 40:
            advice_text = "Valuta con cautela"
            advice_class = "caution"

        else:
            advice_text = "Scegline un'altra"
            advice_class = "poor"

    reasons = card.get("scoreReasons", [])
    warnings = card.get("scoreWarnings", [])

    reasons_html = "".join(
        f"<li>✅ {reason}</li>"
        for reason in reasons
    )

    warnings_html = "".join(
        f"<li>⚠️ {warning}</li>"
        for warning in warnings
    )

    if not reasons_html:
        reasons_html = "<li>Nessun elemento favorevole registrato.</li>"

    if not warnings_html:
        warnings_html = "<li>Nessun avviso registrato.</li>"

    html = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta
            name="viewport"
            content="width=device-width, initial-scale=1"
        >

        <title>{item_id} - AngurIA</title>

        <style>
            body {{
                font-family:
                    -apple-system,
                    BlinkMacSystemFont,
                    "Segoe UI",
                    Arial,
                    sans-serif;

                background: #f4f8f3;
                margin: 0;
                color: #243124;
            }}

            .container {{
                max-width: 900px;
                margin: auto;
                padding: 30px;
            }}

            .back {{
                display: inline-block;
                margin-bottom: 20px;
                color: #2e7d32;
                text-decoration: none;
                font-weight: 700;
            }}

            .panel {{
                background: white;
                padding: 25px;
                border-radius: 20px;
                box-shadow:
                    0 6px 22px rgba(0,0,0,0.07);
            }}

            .photo {{
                width: 100%;
                max-height: 420px;
                object-fit: contain;
                background: #edf3ed;
                border-radius: 16px;
                margin-bottom: 20px;
            }}

            h1 {{
                color: #2e7d32;
            }}

            .score {{
                font-size: 38px;
                font-weight: 800;
                color: #2e7d32;
                margin: 15px 0 12px;
            }}

            .advice {{
                display: inline-block;
                margin-bottom: 25px;
                padding: 10px 16px;
                border-radius: 999px;
                font-weight: 800;
                font-size: 16px;
            }}

            .advice.excellent {{
                background: #dff4e2;
                color: #1b5e20;
            }}

            .advice.good {{
                background: #eef6df;
                color: #4f6b1f;
            }}

            .advice.caution {{
                background: #fff1d6;
                color: #8a5b00;
            }}

            .advice.poor {{
                background: #fde4e4;
                color: #9b1c1c;
            }}

            .advice.neutral {{
                background: #ecefec;
                color: #5f6b5f;
            }}

            .grid {{
                display: grid;
                grid-template-columns:
                    repeat(auto-fit, minmax(240px, 1fr));
                gap: 18px;
            }}

            label {{
                display: block;
                font-weight: 700;
                margin-bottom: 7px;
            }}

            select {{
                width: 100%;
                padding: 12px;
                border:
                    1px solid #ccd8cc;
                border-radius: 10px;
                background: white;
                font-size: 15px;
            }}

            button {{
                margin-top: 25px;
                width: 100%;
                padding: 15px;
                border: 0;
                border-radius: 12px;
                background: #2e7d32;
                color: white;
                font-size: 17px;
                font-weight: 800;
                cursor: pointer;
            }}

            .analysis-block {{
                margin-top: 24px;
                padding: 18px;
                background: #f8fbf7;
                border-radius: 14px;
            }}

            .analysis-block h2 {{
                margin-top: 0;
                font-size: 18px;
                color: #2e7d32;
            }}

            .positive-list,
            .warning-list {{
                margin: 0;
                padding-left: 0;
                list-style: none;
            }}

            .positive-list li,
            .warning-list li {{
                margin: 8px 0;
                line-height: 1.4;
            }}

            .note {{
                margin-top: 20px;
                color: #687668;
                font-size: 13px;
            }}
        </style>
    </head>

    <body>

    <div class="container">

        <a class="back" href="/">
            ← Torna al Dataset Explorer
        </a>

        <div class="panel">

            <h1>🍉 {item_id}</h1>

            <img
                class="photo"
                src="/image/{card.get('photo', '')}"
                alt="{item_id}"
            >

            <div>
                AngurIA Score
            </div>

            <div class="score">
                {score_text}
            </div>

            <div class="advice {advice_class}">
                {advice_text}
            </div>

            <form
                method="post"
                action="/card/{item_id}"
            >

                <div class="grid">

                    <div>
                        <label>Macchia d'appoggio</label>

                        <select name="groundSpot">
                            <option value="">Non valutata</option>

                            <option
                                value="creamy_yellow"
                                {selected("groundSpot", "creamy_yellow")}
                            >
                                Giallo crema
                            </option>

                            <option
                                value="yellow"
                                {selected("groundSpot", "yellow")}
                            >
                                Gialla
                            </option>

                            <option
                                value="light_yellow"
                                {selected("groundSpot", "light_yellow")}
                            >
                                Giallo chiaro
                            </option>

                            <option
                                value="white"
                                {selected("groundSpot", "white")}
                            >
                                Bianca
                            </option>
                        </select>
                    </div>


                    <div>
                        <label>Peduncolo</label>

                        <select name="peduncle">
                            <option value="">Non valutato</option>

                            <option
                                value="dry"
                                {selected("peduncle", "dry")}
                            >
                                Secco
                            </option>

                            <option
                                value="partly_dry"
                                {selected("peduncle", "partly_dry")}
                            >
                                Parzialmente secco
                            </option>

                            <option
                                value="green"
                                {selected("peduncle", "green")}
                            >
                                Verde
                            </option>
                        </select>
                    </div>


                    <div>
                        <label>Forma</label>

                        <select name="shape">
                            <option value="">Non valutata</option>

                            <option
                                value="regular"
                                {selected("shape", "regular")}
                            >
                                Regolare
                            </option>

                            <option
                                value="slightly_irregular"
                                {selected("shape", "slightly_irregular")}
                            >
                                Leggermente irregolare
                            </option>

                            <option
                                value="irregular"
                                {selected("shape", "irregular")}
                            >
                                Irregolare
                            </option>
                        </select>
                    </div>


                    <div>
                        <label>Striature</label>

                        <select name="stripes">
                            <option value="">Non valutate</option>

                            <option
                                value="well_defined"
                                {selected("stripes", "well_defined")}
                            >
                                Ben definite
                            </option>

                            <option
                                value="medium"
                                {selected("stripes", "medium")}
                            >
                                Medie
                            </option>

                            <option
                                value="weak"
                                {selected("stripes", "weak")}
                            >
                                Poco definite
                            </option>
                        </select>
                    </div>


                    <div>
                        <label>Simmetria</label>

                        <select name="symmetry">
                            <option value="">Non valutata</option>

                            <option
                                value="high"
                                {selected("symmetry", "high")}
                            >
                                Alta
                            </option>

                            <option
                                value="medium"
                                {selected("symmetry", "medium")}
                            >
                                Media
                            </option>

                            <option
                                value="low"
                                {selected("symmetry", "low")}
                            >
                                Bassa
                            </option>
                        </select>
                    </div>


                    <div>
                        <label>Colore</label>

                        <select name="color">
                            <option value="">Non valutato</option>

                            <option
                                value="balanced"
                                {selected("color", "balanced")}
                            >
                                Equilibrato
                            </option>

                            <option
                                value="acceptable"
                                {selected("color", "acceptable")}
                            >
                                Accettabile
                            </option>

                            <option
                                value="poor"
                                {selected("color", "poor")}
                            >
                                Poco favorevole
                            </option>
                        </select>
                    </div>


                    <div>
                        <label>Superficie</label>

                        <select name="surface">
                            <option value="">Non valutata</option>

                            <option
                                value="healthy"
                                {selected("surface", "healthy")}
                            >
                                Sana
                            </option>

                            <option
                                value="minor_defects"
                                {selected("surface", "minor_defects")}
                            >
                                Piccoli difetti
                            </option>

                            <option
                                value="damaged"
                                {selected("surface", "damaged")}
                            >
                                Danneggiata
                            </option>
                        </select>
                    </div>

                </div>

                <button type="submit">
                    Salva e calcola AngurIA Score
                </button>

            </form>

            <div class="analysis-block">
                <h2>Punti favorevoli</h2>

                <ul class="positive-list">
                    {reasons_html}
                </ul>
            </div>

            <div class="analysis-block">
                <h2>Aspetti da verificare</h2>

                <ul class="warning-list">
                    {warnings_html}
                </ul>
            </div>

            <div class="note">
                Score sperimentale basato su regole.
                Non rappresenta ancora una previsione
                validata della qualità interna.
            </div>

        </div>

    </div>

    </body>
    </html>
    """

    return HTMLResponse(content=html)


@app.post("/card/{item_id}")
def save_card(
    item_id: str,
    groundSpot: str = Form(""),
    peduncle: str = Form(""),
    shape: str = Form(""),
    stripes: str = Form(""),
    symmetry: str = Form(""),
    color: str = Form(""),
    surface: str = Form(""),
):
    card_path = CARDS_DIR / f"{item_id}.json"

    if not card_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Scheda non trovata",
        )

    with card_path.open("r", encoding="utf-8") as file:
        card = json.load(file)

    card["groundSpot"] = groundSpot
    card["peduncle"] = peduncle
    card["shape"] = shape
    card["stripes"] = stripes
    card["symmetry"] = symmetry
    card["color"] = color
    card["surface"] = surface

    result = calculate_anguria_score(card)

    card["anguriaScore"] = result["score"]
    card["anguriaScoreMax"] = result["maxScore"]
    card["recommendation"] = result["recommendation"]
    card["scoreReasons"] = result["reasons"]
    card["scoreWarnings"] = result["warnings"]
    card["scoreExperimental"] = True
    card["scoreDisclaimer"] = result["disclaimer"]

    with card_path.open("w", encoding="utf-8") as file:
        json.dump(
            card,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return RedirectResponse(
        url=f"/card/{item_id}",
        status_code=303,
    )
