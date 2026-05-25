import time
from dataclasses import replace
from typing import List

import cv2
import numpy as np

from config import settings
from src.hand_tracker import HandInfo, HandTracker, FINGER_NAMES
from src.states.state_manager import StateManager

_KEY_ESC = 27
_KEY_Q = ord("q")
_KEY_F = ord("f")
_KEY_M = ord("m")  # alternar espejo en runtime
_MAX_CAMERA_FAILURES = 60


def _scale_point(p, sx, sy):
    return (int(p[0] * sx), int(p[1] * sy))


def _rescale_hands(hands_info: List[HandInfo], from_size, to_size) -> List[HandInfo]:
    """Reescala todos los puntos de cada HandInfo del sistema de coords
    `from_size = (w, h)` al sistema `to_size = (w, h)`. NO muta los originales."""
    if not hands_info:
        return []
    fw, fh = from_size
    tw, th = to_size
    if fw == tw and fh == th:
        return hands_info
    sx = tw / fw
    sy = th / fh
    out: List[HandInfo] = []
    for h in hands_info:
        new_lms = [_scale_point(pt, sx, sy) for pt in h.landmarks_px]
        new_cur = _scale_point(h.cursor_point, sx, sy) if h.cursor_point else None
        out.append(replace(h, landmarks_px=new_lms, cursor_point=new_cur))
    return out


class InteractiveApp:
    def __init__(self):
        # Inicializar TODO a None primero, para que _cleanup() sea seguro
        self.cap = None
        self.hand_tracker = None
        self.state_manager = None
        self._window_created = False
        self._fullscreen = False
        self._mirror = settings.MIRROR_CAMERA

        # FPS
        self._fps_last_time = time.time()
        self._fps_count = 0
        self._fps_current = 0.0

        # Pre-alocar el fondo: evita asignar 6 MB cada frame
        self._bg_cache = np.full(
            (settings.WINDOW_HEIGHT, settings.WINDOW_WIDTH, 3),
            settings.COLOR_BG, dtype=np.uint8,
        )

        print("[app] Inicializando cámara y entornos gráficos...")
        self.cap = self._init_camera()
        self.hand_tracker = HandTracker(
            max_num_hands=settings.MAX_NUM_HANDS,
            min_detection_confidence=settings.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=settings.MIN_TRACKING_CONFIDENCE,
            min_presence_confidence=getattr(
                settings, "MIN_PRESENCE_CONFIDENCE", None
            ),
        )
        self.state_manager = StateManager()
        self._init_window()

    # ------------------------------------------------------------------
    def _init_camera(self):
        # Usar backend específico (DirectShow en Windows) para arranque rápido
        cap = cv2.VideoCapture(settings.CAMERA_INDEX, settings.CAMERA_BACKEND)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.CAMERA_HEIGHT)
        # Reducir buffer interno: queremos el frame más reciente, no acumular
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not cap.isOpened():
            cap.release()
            raise RuntimeError(
                f"No se pudo abrir la cámara (index={settings.CAMERA_INDEX}). "
                f"Verifique que esté conectada y libre."
            )
        # Reportar resolución real (la cámara puede negociar otra distinta)
        real_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        real_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[app] Cámara abierta a {real_w}x{real_h}")
        return cap

    def _init_window(self):
        cv2.namedWindow(settings.WINDOW_NAME, cv2.WINDOW_NORMAL)
        self._window_created = True
        if settings.FULLSCREEN:
            self._toggle_fullscreen()
        else:
            cv2.resizeWindow(
                settings.WINDOW_NAME, settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT
            )

    def _toggle_fullscreen(self):
        self._fullscreen = not self._fullscreen
        if self._fullscreen:
            cv2.setWindowProperty(
                settings.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
            )
        else:
            cv2.setWindowProperty(
                settings.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL
            )
            cv2.resizeWindow(
                settings.WINDOW_NAME, settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT
            )

    # Loop
    def run(self):
        consecutive_failures = 0
        # Acumuladores para profiling
        t_read = t_proc = t_render = 0.0
        prof_frames = 0
        prof_t0 = time.time()

        try:
            while True:
                t0 = time.perf_counter()
                ok, frame = self.cap.read()
                t1 = time.perf_counter()

                if not ok or frame is None:
                    consecutive_failures += 1
                    if consecutive_failures >= _MAX_CAMERA_FAILURES:
                        print("[app] Sensor de video sin respuesta. Saliendo.")
                        break
                    if cv2.waitKey(10) & 0xFF in (_KEY_ESC, _KEY_Q):
                        break
                    continue
                consecutive_failures = 0

                if self._mirror:
                    frame = cv2.flip(frame, 1)
                cam_h, cam_w = frame.shape[:2]

                pw = settings.PROCESSING_WIDTH
                ph = settings.PROCESSING_HEIGHT
                if (cam_w, cam_h) != (pw, ph):
                    small = cv2.resize(frame, (pw, ph), interpolation=cv2.INTER_LINEAR)
                else:
                    small = frame
                t2 = time.perf_counter()

                hands_info = self.hand_tracker.process(small)
                t3 = time.perf_counter()

                canvas = self._build_canvas(frame)
                canvas_h, canvas_w = canvas.shape[:2]

                # Los landmarks están en coords del frame procesado (pw, ph).
                # Escalar al canvas para el cursor y dibujado.
                hands_info = _rescale_hands(
                    hands_info,
                    from_size=(pw, ph),
                    to_size=(canvas_w, canvas_h),
                )

                if settings.SHOW_HAND_LANDMARKS:
                    self._draw_landmarks(canvas, hands_info)
                if settings.SHOW_EXTENDED_FINGERS_DEBUG:
                    self._draw_extended_fingers_debug(canvas, hands_info)

                self.state_manager.update_and_render(canvas, hands_info)

                if settings.SHOW_FPS:
                    self._draw_fps(canvas)

                cv2.imshow(settings.WINDOW_NAME, canvas)
                t4 = time.perf_counter()

                # Profiling acumulado
                if settings.SHOW_TIMING_PROFILE:
                    t_read += (t1 - t0) + (t2 - t1)  # read + flip + resize
                    t_proc += (t3 - t2)              # mediapipe
                    t_render += (t4 - t3)            # canvas + state + imshow
                    prof_frames += 1
                    if time.time() - prof_t0 >= 2.0:
                        avg_read = 1000 * t_read / prof_frames
                        avg_proc = 1000 * t_proc / prof_frames
                        avg_rend = 1000 * t_render / prof_frames
                        avg_total = avg_read + avg_proc + avg_rend
                        print(
                            f"[profile] cam+resize={avg_read:.1f}ms | "
                            f"mediapipe={avg_proc:.1f}ms | "
                            f"render={avg_rend:.1f}ms | "
                            f"total={avg_total:.1f}ms ({1000/avg_total:.1f} FPS)"
                        )
                        t_read = t_proc = t_render = 0.0
                        prof_frames = 0
                        prof_t0 = time.time()

                key = cv2.waitKey(1) & 0xFF
                if key in (_KEY_ESC, _KEY_Q):
                    break
                elif key == _KEY_F:
                    self._toggle_fullscreen()
                elif key == _KEY_M:
                    self._mirror = not self._mirror
                    print(f"[app] Espejo: {self._mirror}")
        finally:
            self._cleanup()

    # ------------------------------------------------------------------
    def _build_canvas(self, camera_frame):
        """Construye el lienzo. Por defecto fondo blanco TEC. Si está activo
        SHOW_CAMERA_BACKGROUND, mezcla la cámara translúcida sobre el blanco.

        Optimización: el fondo plano se precalcula una vez en __init__ y se
        copia cada frame (np.copyto es mucho más rápido que np.full).
        """
        if settings.SHOW_CAMERA_BACKGROUND:
            tw, th = settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT
            cam_resized = cv2.resize(camera_frame, (tw, th))
            alpha = settings.CAMERA_BACKGROUND_OPACITY
            return cv2.addWeighted(cam_resized, alpha, self._bg_cache, 1.0 - alpha, 0)
        # Fondo plano: copia del cache pre-alocado (rápido)
        canvas = np.empty_like(self._bg_cache)
        np.copyto(canvas, self._bg_cache)
        return canvas

    def _draw_fps(self, canvas):
        self._fps_count += 1
        now = time.time()
        if now - self._fps_last_time >= 1.0:
            self._fps_current = self._fps_count / (now - self._fps_last_time)
            self._fps_count = 0
            self._fps_last_time = now
        cv2.putText(
            canvas, f"FPS: {self._fps_current:.1f}",
            (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
            0.7, settings.COLOR_TEXT, 2, cv2.LINE_AA,
        )

    def _draw_landmarks(self, canvas, hands_info: List[HandInfo]):
        for hand in hands_info:
            for (x, y) in hand.landmarks_px:
                cv2.circle(canvas, (x, y), 5, (0, 200, 0), -1)

    def _draw_extended_fingers_debug(self, canvas, hands_info: List[HandInfo]):
        if not hands_info:
            return
        hand = hands_info[0]
        names = [FINGER_NAMES[i] for i in hand.extended_fingers]
        text = f"Dedos: {names} | Lado: {hand.handedness}"
        cv2.putText(
            canvas, text, (20, canvas.shape[0] - 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, settings.COLOR_ACCENT, 2, cv2.LINE_AA,
        )

    # ------------------------------------------------------------------
    def _cleanup(self):
        """Cleanup seguro: nada revienta si la inicialización falló a medias."""
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception as e:
                print(f"[app] Error liberando cámara: {e}")
        if self.hand_tracker is not None:
            try:
                self.hand_tracker.close()
            except Exception as e:
                print(f"[app] Error cerrando HandTracker: {e}")
        if self._window_created:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
