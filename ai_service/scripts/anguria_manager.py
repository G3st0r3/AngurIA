import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent

LOGS_DIR = BASE_DIR / "logs"
PIDS_DIR = BASE_DIR / ".pids"

DATASET_DIR = BASE_DIR / "datasets" / "watermelon"
IMAGES_DIR = DATASET_DIR / "raw" / "own"
ANNOTATIONS_DIR = DATASET_DIR / "annotations"
CARDS_DIR = DATASET_DIR / "cards"

MODEL_PATH = (
    BASE_DIR
    / "runs"
    / "watermelon_v3"
    / "weights"
    / "best.pt"
)

AI_PID_FILE = PIDS_DIR / "fastapi.pid"
DATASET_PID_FILE = PIDS_DIR / "dataset.pid"
FLUTTER_PID_FILE = PIDS_DIR / "flutter.pid"

AI_LOG_FILE = LOGS_DIR / "fastapi.log"
DATASET_LOG_FILE = LOGS_DIR / "dataset.log"
FLUTTER_LOG_FILE = LOGS_DIR / "flutter.log"


def ensure_runtime_dirs():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    PIDS_DIR.mkdir(parents=True, exist_ok=True)


def count_files(directory, extensions):
    if not directory.exists():
        return 0

    return sum(
        1
        for path in directory.iterdir()
        if path.is_file()
        and path.suffix.lower() in extensions
    )


def service_pid(port):
    result = subprocess.run(
        ["lsof", "-ti", f":{port}"],
        capture_output=True,
        text=True,
    )

    value = result.stdout.strip()

    if not value:
        return None

    try:
        return int(value.splitlines()[0])
    except ValueError:
        return None


def process_exists(pid_file):
    if not pid_file.exists():
        return None

    try:
        pid = int(
            pid_file.read_text(
                encoding="utf-8"
            ).strip()
        )
    except ValueError:
        return None

    try:
        os.kill(pid, 0)
        return pid
    except OSError:
        return None


def command_status():
    images = count_files(
        IMAGES_DIR,
        {".jpg", ".jpeg", ".png", ".webp"},
    )

    annotations = count_files(
        ANNOTATIONS_DIR,
        {".txt"},
    )

    cards = count_files(
        CARDS_DIR,
        {".json"},
    )

    print()
    print("🍉 ANGURIA SYSTEM STATUS")
    print("=" * 42)

    print(f"Immagini dataset : {images}")
    print(f"Schede JSON      : {cards}")
    print(f"Annotazioni YOLO : {annotations}")
    print()

    if MODEL_PATH.exists():
        print("✅ Modello watermelon_v3 presente")
    else:
        print("❌ Modello watermelon_v3 NON trovato")

    ai_pid = service_pid(8000)
    dataset_pid = service_pid(8001)
    flutter_pid = process_exists(
        FLUTTER_PID_FILE
    )

    if ai_pid:
        print(
            f"🟢 FastAPI AI       : ONLINE "
            f"(PID {ai_pid})"
        )
    else:
        print("⚪ FastAPI AI       : OFFLINE")

    if dataset_pid:
        print(
            f"🟢 Dataset Explorer : ONLINE "
            f"(PID {dataset_pid})"
        )
    else:
        print("⚪ Dataset Explorer : OFFLINE")

    if flutter_pid:
        print(
            f"🟢 Flutter Web      : ONLINE "
            f"(PID {flutter_pid})"
        )
    else:
        print("⚪ Flutter Web      : OFFLINE")

    print("=" * 42)
    print()


def start_uvicorn(
    module,
    port,
    pid_file,
    log_file,
    label,
):
    if service_pid(port):
        print(f"✅ {label} già attivo")
        return

    handle = log_file.open(
        "a",
        encoding="utf-8",
    )

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            module,
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=BASE_DIR,
        stdout=handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

    pid_file.write_text(
        str(process.pid),
        encoding="utf-8",
    )

    time.sleep(2)

    if service_pid(port):
        print(f"🟢 {label} avviato")
    else:
        print(
            f"❌ {label} non avviato. "
            f"Controlla {log_file}"
        )


def start_flutter():
    existing_pid = process_exists(
        FLUTTER_PID_FILE
    )

    if existing_pid:
        print("✅ Flutter già attivo")
        return

    handle = FLUTTER_LOG_FILE.open(
        "a",
        encoding="utf-8",
    )

    process = subprocess.Popen(
        [
            "flutter",
            "run",
            "-d",
            "chrome",
        ],
        cwd=PROJECT_DIR,
        stdout=handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

    FLUTTER_PID_FILE.write_text(
        str(process.pid),
        encoding="utf-8",
    )

    print(
        "🟢 Avvio Flutter richiesto "
        "(Chrome può impiegare qualche secondo)"
    )


def command_start():
    ensure_runtime_dirs()

    print()
    print("🍉 AVVIO ANGURIA")
    print("=" * 32)

    start_uvicorn(
        "app:app",
        8000,
        AI_PID_FILE,
        AI_LOG_FILE,
        "FastAPI AI",
    )

    start_uvicorn(
        "dataset_dashboard:app",
        8001,
        DATASET_PID_FILE,
        DATASET_LOG_FILE,
        "Dataset Explorer",
    )

    start_flutter()

    print()
    command_status()


def stop_pid_file(
    pid_file,
    label,
):
    pid = process_exists(pid_file)

    if not pid:
        print(f"⚪ {label} già fermo")
        pid_file.unlink(
            missing_ok=True
        )
        return

    try:
        os.kill(
            pid,
            signal.SIGTERM,
        )

        print(
            f"🛑 Arresto {label} "
            f"(PID {pid})"
        )

    except ProcessLookupError:
        pass

    time.sleep(1)

    pid_file.unlink(
        missing_ok=True
    )


def stop_port(
    port,
    pid_file,
    label,
):
    pid = service_pid(port)

    if not pid:
        print(f"⚪ {label} già fermo")
        pid_file.unlink(
            missing_ok=True
        )
        return

    try:
        os.kill(
            pid,
            signal.SIGTERM,
        )

        print(
            f"🛑 Arresto {label} "
            f"(PID {pid})"
        )

    except ProcessLookupError:
        pass

    time.sleep(1)

    pid_file.unlink(
        missing_ok=True
    )


def command_stop():
    ensure_runtime_dirs()

    print()
    print("🍉 ARRESTO ANGURIA")
    print("=" * 32)

    stop_pid_file(
        FLUTTER_PID_FILE,
        "Flutter Web",
    )

    stop_port(
        8001,
        DATASET_PID_FILE,
        "Dataset Explorer",
    )

    stop_port(
        8000,
        AI_PID_FILE,
        "FastAPI AI",
    )

    print()
    command_status()


def run_script(filename):
    script = BASE_DIR / "scripts" / filename

    if not script.exists():
        print(
            f"❌ Script non trovato: "
            f"{filename}"
        )
        sys.exit(1)

    subprocess.run(
        [
            sys.executable,
            str(script),
        ],
        check=True,
        cwd=BASE_DIR,
    )


def command_train():
    print()
    print("🧠 Avvio training AngurIA...")
    run_script("train_model.py")


def main():
    parser = argparse.ArgumentParser(
        description="AngurIA Manager"
    )

    parser.add_argument(
        "command",
        choices=[
            "status",
            "start",
            "stop",
            "train",
        ],
    )

    args = parser.parse_args()

    if args.command == "status":
        command_status()
    elif args.command == "start":
        command_start()
    elif args.command == "stop":
        command_stop()
    elif args.command == "train":
        command_train()


if __name__ == "__main__":
    main()
