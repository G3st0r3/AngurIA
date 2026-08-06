import sys
from pathlib import Path

from ultralytics import YOLO


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python detect_watermelon.py /percorso/foto.jpg")
        raise SystemExit(1)

    image_path = Path(sys.argv[1]).expanduser().resolve()

    if not image_path.exists():
        print(f"Errore: immagine non trovata: {image_path}")
        raise SystemExit(1)

    print("Caricamento modello YOLO-World...")

    model = YOLO("yolov8s-world.pt")

    model.set_classes(
        [
            "watermelon",
            "whole watermelon",
            "green striped watermelon",
            "watermelon fruit",
            "round green melon",
        ]
    )

    print(f"Analisi immagine: {image_path.name}")

    results = model.predict(
        source=str(image_path),
        conf=0.03,
        iou=0.40,
        imgsz=960,
        save=True,
        project="runs",
        name="watermelon_detection",
        exist_ok=True,
        verbose=False,
    )

    result = results[0]
    boxes = result.boxes

    if boxes is None or len(boxes) == 0:
        print("Nessuna anguria rilevata.")
        print(
            "Prova una foto con il frutto intero, ben illuminato "
            "e con poco sfondo."
        )
        return

    print(f"Rilevamenti trovati: {len(boxes)}")

    for index, box in enumerate(boxes, start=1):
        confidence = float(box.conf[0])
        class_id = int(box.cls[0])

        label = result.names.get(class_id, "oggetto")

        x1, y1, x2, y2 = [
            int(value) for value in box.xyxy[0].tolist()
        ]

        width = x2 - x1
        height = y2 - y1

        print(f"\nRilevamento {index}")
        print(f"Etichetta: {label}")
        print(f"Confidenza: {confidence * 100:.1f}%")
        print(f"x: {x1}")
        print(f"y: {y1}")
        print(f"larghezza: {width}")
        print(f"altezza: {height}")

    print(
        "\nImmagine con rettangolo salvata nella cartella "
        "ai_service/runs/watermelon_detection/"
    )


if __name__ == "__main__":
    main()