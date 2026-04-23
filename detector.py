import argparse
import sys
import threading
import queue
from pathlib import Path

import cv2
from ultralytics import YOLO

MODEL_PATH = Path(__file__).parent / "models" / "best.pt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mechdog — Detector de objetos via cámara IP",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--ip",
        required=True,
        help="IP del celular (ej: 210.139.240.31)",
    )
    parser.add_argument(
        "--port",
        default=8080,
        type=int,
        help="Puerto de la app de cámara (default: 8080)",
    )
    parser.add_argument(
        "--stream",
        default="video",
        help="Ruta del stream (default: 'video')\n"
             "IP Webcam usa 'video', DroidCam puede usar 'videofeed'",
    )
    parser.add_argument(
        "--conf",
        default=0.5,
        type=float,
        help="Umbral de confianza para detección (default: 0.5)",
    )
    parser.add_argument(
        "--no-detect",
        action="store_true",
        help="Iniciar sin detección activa (activá con 'd')",
    )
    return parser.parse_args()


def build_url(ip: str, port: int, stream: str) -> str:
    return f"http://{ip}:{port}/{stream}"


def draw_status(frame, detecting: bool) -> None:
    label = "Deteccion: ON" if detecting else "Deteccion: OFF"
    color = (0, 220, 0) if detecting else (0, 60, 220)
    cv2.putText(frame, label, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2, cv2.LINE_AA)
    cv2.putText(frame, "d: toggle  |  q: salir", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1, cv2.LINE_AA)


def capture_frames(url: str, frame_queue: queue.Queue, stop_event: threading.Event) -> None:
    """Hilo dedicado a leer frames — descarta los viejos para no acumular delay."""
    cap = cv2.VideoCapture(url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        stop_event.set()
        return

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            cap.open(url)
            continue
        # Siempre quedarse con el frame más reciente
        if not frame_queue.empty():
            try:
                frame_queue.get_nowait()
            except queue.Empty:
                pass
        frame_queue.put(frame)

    cap.release()


def run(ip: str, port: int, stream: str, conf: float, detecting: bool) -> None:
    url = build_url(ip, port, stream)
    print(f"[mechdog] Cargando modelo: {MODEL_PATH}")

    if not MODEL_PATH.exists():
        print(f"[ERROR] Modelo no encontrado en {MODEL_PATH}")
        sys.exit(1)

    model = YOLO(str(MODEL_PATH))

    print(f"[mechdog] Conectando a: {url}")

    frame_queue: queue.Queue = queue.Queue(maxsize=1)
    stop_event = threading.Event()

    capture_thread = threading.Thread(target=capture_frames, args=(url, frame_queue, stop_event), daemon=True)
    capture_thread.start()

    # Esperar primer frame para confirmar conexión
    try:
        frame_queue.get(timeout=5)
    except queue.Empty:
        print(f"[ERROR] No se pudo conectar a {url}")
        print("  Verificá que la app de cámara esté corriendo y la IP/puerto sean correctos.")
        stop_event.set()
        sys.exit(1)

    print("[mechdog] Conectado.")
    print("  Controles: 'd' toggle detección  |  'q' salir")

    while True:
        try:
            frame = frame_queue.get(timeout=2)
        except queue.Empty:
            print("[WARN] Sin frames, esperando...")
            continue

        if detecting:
            results = model(frame, conf=conf, verbose=False)
            frame = results[0].plot()

        draw_status(frame, detecting)
        cv2.imshow("Mechdog Detector", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("d"):
            detecting = not detecting
            state = "activada" if detecting else "desactivada"
            print(f"[mechdog] Detección {state}")

    stop_event.set()
    cv2.destroyAllWindows()
    print("[mechdog] Cerrado.")


def main() -> None:
    args = parse_args()
    run(
        ip=args.ip,
        port=args.port,
        stream=args.stream,
        conf=args.conf,
        detecting=not args.no_detect,
    )


if __name__ == "__main__":
    main()
