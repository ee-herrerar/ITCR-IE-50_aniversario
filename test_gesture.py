import sys
from pathlib import Path

import cv2

# Asegurar que la raíz del proyecto esté en sys.path, igual que run.py
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import settings
from src.hand_tracker import HandTracker, FINGER_NAMES


def main():
    tracker = HandTracker(
        max_num_hands=settings.MAX_NUM_HANDS,
        min_detection_confidence=settings.MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=settings.MIN_TRACKING_CONFIDENCE,
    )

    cap = cv2.VideoCapture(settings.CAMERA_INDEX, settings.CAMERA_BACKEND)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.CAMERA_HEIGHT)

    if not cap.isOpened():
        print("[test] No se pudo abrir la camara.")
        return

    print("[test] Camara abierta. ESC o 'q' para salir.")
    win = "Diagnostico de gesto - una mano un dedo"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)

    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            continue

        if settings.MIRROR_CAMERA:
            frame = cv2.flip(frame, 1)

        hands = tracker.process(frame)

        if hands:
            hand = hands[0]
            # Dibujar todos los landmarks
            for (x, y) in hand.landmarks_px:
                cv2.circle(frame, (x, y), 4, (0, 200, 0), -1)

            names = [FINGER_NAMES[i] for i in hand.extended_fingers]
            cv2.putText(
                frame, f"Extendidos: {names}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2, cv2.LINE_AA,
            )
            cv2.putText(
                frame, f"Mano: {hand.handedness}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2, cv2.LINE_AA,
            )

            if hand.cursor_point is not None:
                # Gesto valido: marcar la punta del indice
                cv2.circle(frame, hand.cursor_point, 18, (0, 255, 0), -1)
                cv2.putText(
                    frame, "GESTO VALIDO", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA,
                )
            else:
                cv2.putText(
                    frame, "SIN GESTO", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA,
                )
        else:
            cv2.putText(
                frame, "SIN MANO", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA,
            )

        cv2.imshow(win, frame)
        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord("q")):
            break

    cap.release()
    cv2.destroyAllWindows()
    tracker.close()


if __name__ == "__main__":
    main()
