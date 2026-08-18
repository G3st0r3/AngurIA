from pathlib import Path
import cv2
import json
import numpy as np

BASE = Path(__file__).resolve().parent.parent / "datasets" / "watermelon"
RAW = BASE / "raw" / "external"
ANN = BASE / "annotations"
CARDS = BASE / "cards"
PREV = BASE / "annotation_previews"

for d in (ANN, PREV):
    d.mkdir(parents=True, exist_ok=True)

for item_id in ("ANG0011", "ANG0012"):
    img_path = RAW / f"{item_id}.jpg"
    img = cv2.imread(str(img_path))

    if img is None:
        print(f"❌ {item_id}: immagine non trovata")
        continue

    h, w = img.shape[:2]
    scale = min(1.0, 1200 / max(h, w))

    small = cv2.resize(
        img, None,
        fx=scale, fy=scale,
        interpolation=cv2.INTER_AREA
    )

    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(
        hsv,
        np.array([20, 20, 15]),
        np.array([105, 255, 255])
    )

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (15, 15)
    )

    mask = cv2.morphologyEx(
        mask, cv2.MORPH_CLOSE, kernel, iterations=3
    )

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    candidates = []

    for c in contours:
        area = cv2.contourArea(c)
        if area < small.shape[0] * small.shape[1] * 0.03:
            continue

        x, y, bw, bh = cv2.boundingRect(c)
        candidates.append((area, x, y, bw, bh))

    if not candidates:
        print(f"⚠️ {item_id}: nessun box trovato")
        continue

    candidates.sort(reverse=True)

    selected = None

    for _, x, y, bw, bh in candidates:
        box_ratio = (
            bw * bh
        ) / (
            small.shape[0]
            * small.shape[1]
        )

        if box_ratio >= 0.90:
            continue

        selected = (
            x,
            y,
            bw,
            bh,
        )
        break

    if selected is None:
        print(
            f"⚠️ {item_id}: "
            "solo box troppo grande, scartato"
        )
        continue

    x, y, bw, bh = selected

    x = int(x / scale)
    y = int(y / scale)
    bw = int(bw / scale)
    bh = int(bh / scale)

    mx = int(bw * 0.04)
    my = int(bh * 0.04)

    x = max(0, x - mx)
    y = max(0, y - my)
    bw = min(w - x, bw + mx * 2)
    bh = min(h - y, bh + my * 2)

    cx = (x + bw / 2) / w
    cy = (y + bh / 2) / h
    nw = bw / w
    nh = bh / h

    (ANN / f"{item_id}.txt").write_text(
        f"0 {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}\n"
    )

    preview = img.copy()
    cv2.rectangle(
        preview,
        (x, y),
        (x + bw, y + bh),
        (0, 255, 0),
        6
    )

    cv2.imwrite(
        str(PREV / f"{item_id}_preview.jpg"),
        preview
    )

    card_path = CARDS / f"{item_id}.json"
    if card_path.exists():
        card = json.loads(card_path.read_text())
        card["trainingStatus"] = "annotated"
        card_path.write_text(
            json.dumps(card, indent=2, ensure_ascii=False)
        )

    print(f"✅ {item_id}: box=({x},{y},{bw},{bh})")

print("🍉 Annotazione automatica completata")
