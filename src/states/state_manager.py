"""
Gestión de estados de la experiencia interactiva.

Estados:
    - IdleState: pantalla de espera con invitación a interactuar.
    - MenuState: menú radial parametrizado (sirve para menú principal y submenús).
    - VideoState: reproduce un video con botón "Volver" por dwell.

Toda la paleta sale de config/settings.py. Si quieres cambiar colores, ahí está.
"""
import math
import time
from typing import List, Optional, Tuple

import cv2

from config import settings
from config import content
from src.hand_tracker import HandInfo


# ===========================================================================
# Utilidades
# ===========================================================================
class CursorSmoother:
    """Filtro exponencial para suavizar el movimiento del cursor."""

    def __init__(self, alpha: float):
        self.alpha = alpha
        self._pos: Optional[Tuple[float, float]] = None

    def update(self, new_pos: Optional[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        if new_pos is None:
            self._pos = None
            return None
        if self._pos is None:
            self._pos = (float(new_pos[0]), float(new_pos[1]))
        else:
            a = self.alpha
            self._pos = (
                a * self._pos[0] + (1.0 - a) * new_pos[0],
                a * self._pos[1] + (1.0 - a) * new_pos[1],
            )
        return (int(self._pos[0]), int(self._pos[1]))


def _draw_text_centered(canvas, text, center, font_scale=0.7,
                        color=None, thickness=2):
    if color is None:
        color = settings.COLOR_TEXT
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), _ = cv2.getTextSize(text, font, font_scale, thickness)
    org = (center[0] - tw // 2, center[1] + th // 2)
    cv2.putText(canvas, text, org, font, font_scale, color, thickness, cv2.LINE_AA)


def _hypot(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _draw_dwell_ring(canvas, center, radius, progress):
    """Dibuja un anillo de progreso (0..1) alrededor de un punto."""
    if progress <= 0:
        return
    end_angle = -90 + int(progress * 360)
    cv2.ellipse(
        canvas, center, (radius + 8, radius + 8),
        0, -90, end_angle, settings.COLOR_ACCENT, 4, cv2.LINE_AA,
    )


# ===========================================================================
# Base
# ===========================================================================
class BaseState:
    def __init__(self, manager):
        self.manager = manager

    def update_and_render(self, canvas, hands_info: List[HandInfo]):
        raise NotImplementedError


# ===========================================================================
# Idle
# ===========================================================================
class IdleState(BaseState):
    """Pantalla de espera; transiciona al menú al detectar gesto válido."""

    def __init__(self, manager):
        super().__init__(manager)
        self._t_start = time.time()

    def update_and_render(self, canvas, hands_info: List[HandInfo]):
        h, w = canvas.shape[:2]
        cx, cy = w // 2, h // 2

        # Pulso suave alrededor del nodo central
        t = time.time() - self._t_start
        ring_r = int(settings.CENTER_NODE_RADIUS * 1.4
                     + 6 * math.sin(t * 1.8))

        cv2.circle(canvas, (cx, cy), ring_r, settings.COLOR_ACCENT, 2, cv2.LINE_AA)
        cv2.circle(canvas, (cx, cy), settings.CENTER_NODE_RADIUS,
                   settings.COLOR_CENTER_NODE, -1, cv2.LINE_AA)

        _draw_text_centered(
            canvas, "TEC", (cx, cy),
            font_scale=1.3, color=settings.COLOR_TEXT_ON_DARK, thickness=3,
        )
        _draw_text_centered(
            canvas, "Ingenieria Electronica", (cx, cy + 230),
            font_scale=1.0, color=settings.COLOR_TEXT, thickness=2,
        )
        _draw_text_centered(
            canvas, "Levante un dedo para iniciar", (cx, cy + 280),
            font_scale=0.7, color=settings.COLOR_TEXT, thickness=1,
        )

        # Transición: en cuanto haya un cursor válido, pasamos al menú principal
        if hands_info and hands_info[0].cursor_point is not None:
            self.manager.go_to_main_menu()


# ===========================================================================
# Menú radial (principal y submenús)
# ===========================================================================
class MenuState(BaseState):
    def __init__(self, manager, options: List[dict],
                 is_submenu: bool = False, title: str = ""):
        super().__init__(manager)
        self.options = options
        self.is_submenu = is_submenu
        self.title = title

        # Hover/dwell de nodos (separado del back, para evitar contaminación)
        self._hover_idx: Optional[int] = None
        self._hover_start: Optional[float] = None
        # Hover/dwell exclusivo del botón Volver
        self._back_start: Optional[float] = None

        self._last_active = time.time()

        if is_submenu:
            self.orbit = settings.ORBIT_RADIUS_SUB
            self.node_r = settings.NODE_RADIUS_SUB
        else:
            self.orbit = settings.ORBIT_RADIUS_MAIN
            self.node_r = settings.NODE_RADIUS_MAIN

    def update_and_render(self, canvas, hands_info: List[HandInfo]):
        now = time.time()
        h, w = canvas.shape[:2]
        cx, cy = w // 2, h // 2

        raw_cursor = (hands_info[0].cursor_point
                      if hands_info and len(hands_info) == 1 else None)
        cursor = self.manager.smoother.update(raw_cursor)

        if cursor is not None:
            self._last_active = now
        elif now - self._last_active > settings.IDLE_TIMEOUT_SECONDS:
            self.manager.go_to_idle()
            return

        # ---- posiciones de nodos ----
        n = len(self.options)
        positions = []
        for i in range(n):
            angle = (2 * math.pi * i / n) - (math.pi / 2)
            nx = int(cx + self.orbit * math.cos(angle))
            ny = int(cy + self.orbit * math.sin(angle))
            positions.append((nx, ny))

        # ---- hover sobre nodos ----
        hover_idx = None
        if cursor is not None:
            for i, pos in enumerate(positions):
                if _hypot(cursor, pos) < self.node_r:
                    hover_idx = i
                    break

        # ---- hover sobre botón Volver ----
        back_hover = False
        if self.is_submenu and cursor is not None:
            back_hover = _hypot(cursor, settings.BACK_BUTTON_POS) < settings.BACK_BUTTON_RADIUS

        # ---- gestión del dwell de nodos ----
        if hover_idx is not None:
            if self._hover_idx == hover_idx:
                if now - self._hover_start >= settings.DWELL_TIME_SECONDS:
                    self._trigger(self.options[hover_idx])
                    return
            else:
                self._hover_idx = hover_idx
                self._hover_start = now
        else:
            self._hover_idx = None
            self._hover_start = None

        # ---- gestión del dwell del Volver ----
        if back_hover:
            if self._back_start is None:
                self._back_start = now
            elif now - self._back_start >= settings.BACK_DWELL_TIME:
                self.manager.go_to_main_menu()
                return
        else:
            self._back_start = None

        # ---- render ----
        self._render(canvas, (cx, cy), positions, cursor, back_hover, now)

    # ----- render helpers -----
    def _render(self, canvas, center, positions, cursor, back_hover, now):
        cx, cy = center

        # Título (solo submenú)
        if self.is_submenu and self.title:
            cv2.putText(
                canvas, self.title, (50, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, settings.COLOR_TEXT, 3, cv2.LINE_AA,
            )

        # Líneas radiales (decoración)
        for pos in positions:
            cv2.line(canvas, center, pos, settings.TEC_GRIS_CLARO, 2, cv2.LINE_AA)

        # Nodo central
        cv2.circle(canvas, center, settings.CENTER_NODE_RADIUS,
                   settings.COLOR_CENTER_NODE, -1, cv2.LINE_AA)
        center_label = "Menu" if not self.is_submenu else "TEC"
        _draw_text_centered(
            canvas, center_label, center,
            font_scale=1.0, color=settings.COLOR_TEXT_ON_DARK, thickness=2,
        )

        # Nodos de opciones
        for i, pos in enumerate(positions):
            opt = self.options[i]
            is_hover = (self._hover_idx == i)

            base_color = settings.COLOR_AREA_NODE
            if "vertiente" in opt and opt["vertiente"] in content.VERTIENTES:
                base_color = content.VERTIENTES[opt["vertiente"]]["color"]
            color = settings.COLOR_AREA_NODE_HOVER if is_hover else base_color

            cv2.circle(canvas, pos, self.node_r, color, -1, cv2.LINE_AA)
            cv2.circle(canvas, pos, self.node_r, settings.COLOR_CENTER_NODE, 2, cv2.LINE_AA)

            # Anillo de progreso de dwell
            if is_hover and self._hover_start is not None:
                progress = min(1.0, (now - self._hover_start) / settings.DWELL_TIME_SECONDS)
                _draw_dwell_ring(canvas, pos, self.node_r, progress)

            # Etiqueta debajo del nodo
            label = opt.get("label", opt.get("id", ""))
            label_pos = (pos[0], pos[1] + self.node_r + 26)
            _draw_text_centered(
                canvas, label, label_pos,
                font_scale=0.55, color=settings.COLOR_TEXT, thickness=1,
            )

        # Botón Volver (solo submenú)
        if self.is_submenu:
            bx, by = settings.BACK_BUTTON_POS
            br = settings.BACK_BUTTON_RADIUS
            color = settings.COLOR_AREA_NODE_HOVER if back_hover else settings.COLOR_AREA_NODE
            cv2.circle(canvas, (bx, by), br, color, -1, cv2.LINE_AA)
            cv2.circle(canvas, (bx, by), br, settings.COLOR_CENTER_NODE, 2, cv2.LINE_AA)
            _draw_text_centered(
                canvas, "Volver", (bx, by),
                font_scale=0.55, color=settings.COLOR_TEXT, thickness=1,
            )
            if back_hover and self._back_start is not None:
                p = min(1.0, (now - self._back_start) / settings.BACK_DWELL_TIME)
                _draw_dwell_ring(canvas, (bx, by), br, p)

        # Cursor
        if cursor is not None:
            cv2.circle(canvas, cursor, settings.CURSOR_RADIUS,
                       settings.COLOR_CURSOR, -1, cv2.LINE_AA)
            cv2.circle(canvas, cursor, settings.CURSOR_RADIUS + 3,
                       settings.TEC_BLANCO, 2, cv2.LINE_AA)

    def _trigger(self, opt):
        action = opt.get("action")
        if action == "play_video":
            self.manager.go_to_video(opt["video"], return_to_submenu=self.is_submenu)
        elif action == "open_submenu":
            sub_id = opt.get("id")
            options = content.SUBMENUS.get(sub_id, [])
            self.manager.go_to_submenu(options, title=opt.get("label", ""))


# ===========================================================================
# Video
# ===========================================================================
class VideoState(BaseState):
    def __init__(self, manager, video_filename: str,
                 return_to_submenu_options=None):
        super().__init__(manager)
        self.video_filename = video_filename
        self.return_to_submenu_options = return_to_submenu_options
        self.video_path = settings.VIDEOS_DIR / video_filename
        self.cap = cv2.VideoCapture(str(self.video_path))
        if not self.cap.isOpened():
            print(f"[video_state] No se pudo abrir: {self.video_path}")
        self._back_start: Optional[float] = None

    def update_and_render(self, canvas, hands_info: List[HandInfo]):
        now = time.time()
        h, w = canvas.shape[:2]

        ok, frame = self.cap.read()
        if not ok or frame is None:
            # Rebobinar y reintentar; si igual falla, mostrar mensaje
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self.cap.read()
        if ok and frame is not None:
            canvas[:] = cv2.resize(frame, (w, h))
        else:
            canvas[:] = settings.COLOR_BG
            _draw_text_centered(
                canvas, f"[Video no disponible: {self.video_filename}]",
                (w // 2, h // 2), font_scale=1.0,
            )

        raw_cursor = (hands_info[0].cursor_point
                      if hands_info and len(hands_info) == 1 else None)
        cursor = self.manager.smoother.update(raw_cursor)

        bx, by = settings.BACK_BUTTON_POS
        br = settings.BACK_BUTTON_RADIUS
        back_hover = (cursor is not None and
                      _hypot(cursor, (bx, by)) < br)

        if back_hover:
            if self._back_start is None:
                self._back_start = now
            elif now - self._back_start >= settings.BACK_DWELL_TIME:
                self._exit_video()
                return
        else:
            self._back_start = None

        # Botón Volver (sobre video — borde blanco para legibilidad)
        color = settings.COLOR_AREA_NODE_HOVER if back_hover else settings.TEC_BLANCO
        cv2.circle(canvas, (bx, by), br, color, -1, cv2.LINE_AA)
        cv2.circle(canvas, (bx, by), br, settings.COLOR_CENTER_NODE, 2, cv2.LINE_AA)
        _draw_text_centered(
            canvas, "Menu", (bx, by),
            font_scale=0.55, color=settings.COLOR_TEXT, thickness=1,
        )
        if back_hover and self._back_start is not None:
            p = min(1.0, (now - self._back_start) / settings.BACK_DWELL_TIME)
            _draw_dwell_ring(canvas, (bx, by), br, p)

        # Cursor
        if cursor is not None:
            cv2.circle(canvas, cursor, settings.CURSOR_RADIUS,
                       settings.COLOR_CURSOR, -1, cv2.LINE_AA)
            cv2.circle(canvas, cursor, settings.CURSOR_RADIUS + 3,
                       settings.TEC_BLANCO, 2, cv2.LINE_AA)

    def _exit_video(self):
        if self.cap is not None:
            self.cap.release()
        if self.return_to_submenu_options is not None:
            self.manager.go_to_submenu(self.return_to_submenu_options)
        else:
            self.manager.go_to_main_menu()


# ===========================================================================
# StateManager
# ===========================================================================
class StateManager:
    def __init__(self):
        self.smoother = CursorSmoother(alpha=settings.CURSOR_SMOOTHING)
        self._state: Optional[BaseState] = None
        self._current_submenu_options = None
        self._current_submenu_title = ""
        self.go_to_idle()

    def go_to_idle(self):
        self._current_submenu_options = None
        self._current_submenu_title = ""
        self._state = IdleState(self)

    def go_to_main_menu(self):
        self._current_submenu_options = None
        self._current_submenu_title = ""
        self._state = MenuState(
            self, options=content.MAIN_MENU_OPTIONS, is_submenu=False,
        )

    def go_to_submenu(self, options, title=""):
        if title:
            self._current_submenu_title = title
        self._current_submenu_options = options
        self._state = MenuState(
            self, options=options, is_submenu=True,
            title=self._current_submenu_title,
        )

    def go_to_video(self, video_filename: str, return_to_submenu: bool = False):
        opts = self._current_submenu_options if return_to_submenu else None
        self._state = VideoState(
            self, video_filename, return_to_submenu_options=opts,
        )

    def update_and_render(self, canvas, hands_info):
        if self._state is not None:
            self._state.update_and_render(canvas, hands_info)
