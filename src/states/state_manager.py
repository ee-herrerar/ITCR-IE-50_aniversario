"""
Gestión de estados de la experiencia interactiva.

Estados:
    - IdleState:     Pantalla de espera con invitación a interactuar.
    - MenuState:     Menú radial parametrizado (menú principal y submenús de áreas).
    - DemoMenuState: Grid táctil de demos; al seleccionar una, escribe state.json
                     para que el watchdog la lance y registra el acceso en access_log.jsonl.
    - VideoState:    Reproduce un video con botón "Volver" por dwell.

Paleta y dimensiones: config/settings.py
Contenido:            config/content.py
"""

import json
import math
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import cv2

from config import content, settings
from src.hand_tracker import HandInfo


# ===========================================================================
# Utilidades compartidas
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
    """Arco de progreso (0..1) alrededor de un punto."""
    if progress <= 0:
        return
    end_angle = -90 + int(progress * 360)
    cv2.ellipse(
        canvas, center, (radius + 8, radius + 8),
        0, -90, end_angle, settings.COLOR_ACCENT, 4, cv2.LINE_AA,
    )


def _write_state(launch_target: str) -> None:
    """Escribe state.json en la raíz del proyecto para que el watchdog lance la demo."""
    state_path = settings.ROOT_DIR / "state.json"
    state = {"launch_target": launch_target}
    state_path.write_text(json.dumps(state), encoding="utf-8")
    print(f"[state_manager] state.json escrito en: {state_path}")


def _log_access(demo_id: str, demo_label: str, script: str) -> None:
    """Agrega una línea al registro de accesos (JSONL)."""
    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "demo_id":    demo_id,
        "demo_label": demo_label,
        "script":     script,
    }
    try:
        with open(settings.ACCESS_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"[state_manager] No se pudo escribir el log de accesos: {exc}")


# ===========================================================================
# Base
# ===========================================================================

class BaseState:
    def __init__(self, manager):
        self.manager = manager

    def update_and_render(self, canvas, hands_info: List[HandInfo]):
        raise NotImplementedError


# ===========================================================================
# IdleState
# ===========================================================================

class IdleState(BaseState):
    """Pantalla de espera; transiciona al menú al detectar gesto válido."""

    def __init__(self, manager):
        super().__init__(manager)
        self._t_start = time.time()

    def update_and_render(self, canvas, hands_info: List[HandInfo]):
        h, w = canvas.shape[:2]
        cx, cy = w // 2, h // 2

        t = time.time() - self._t_start
        ring_r = int(settings.CENTER_NODE_RADIUS * 1.4 + 6 * math.sin(t * 1.8))

        cv2.circle(canvas, (cx, cy), ring_r, settings.COLOR_ACCENT, 2, cv2.LINE_AA)
        cv2.circle(canvas, (cx, cy), settings.CENTER_NODE_RADIUS,
                   settings.COLOR_CENTER_NODE, -1, cv2.LINE_AA)

        _draw_text_centered(canvas, "TEC", (cx, cy),
                            font_scale=1.3, color=settings.COLOR_TEXT_ON_DARK, thickness=3)
        _draw_text_centered(canvas, "Ingenieria Electronica", (cx, cy + 230),
                            font_scale=1.0, color=settings.COLOR_TEXT, thickness=2)
        _draw_text_centered(canvas, "Levante un dedo para iniciar", (cx, cy + 280),
                            font_scale=0.7, color=settings.COLOR_TEXT, thickness=1)

        if hands_info and hands_info[0].cursor_point is not None:
            self.manager.go_to_main_menu()


# ===========================================================================
# MenuState  (radial — menú principal y submenús de áreas)
# ===========================================================================

class MenuState(BaseState):
    def __init__(self, manager, options: List[dict],
                 is_submenu: bool = False, title: str = ""):
        super().__init__(manager)
        self.options    = options
        self.is_submenu = is_submenu
        self.title      = title

        self._hover_idx:   Optional[int]   = None
        self._hover_start: Optional[float] = None
        self._back_start:  Optional[float] = None
        self._last_active = time.time()

        self.orbit  = settings.ORBIT_RADIUS_SUB  if is_submenu else settings.ORBIT_RADIUS_MAIN
        self.node_r = settings.NODE_RADIUS_SUB   if is_submenu else settings.NODE_RADIUS_MAIN

    # ------------------------------------------------------------------
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

        # Posiciones en órbita
        n = len(self.options)
        positions = []
        for i in range(n):
            angle = (2 * math.pi * i / n) - (math.pi / 2)
            positions.append((
                int(cx + self.orbit * math.cos(angle)),
                int(cy + self.orbit * math.sin(angle)),
            ))

        # Hover nodos
        hover_idx = None
        if cursor is not None:
            for i, pos in enumerate(positions):
                if _hypot(cursor, pos) < self.node_r:
                    hover_idx = i
                    break

        # Hover Volver
        back_hover = (self.is_submenu and cursor is not None
                      and _hypot(cursor, settings.BACK_BUTTON_POS) < settings.BACK_BUTTON_RADIUS)

        # Dwell nodos
        if hover_idx is not None:
            if self._hover_idx == hover_idx:
                if now - self._hover_start >= settings.DWELL_TIME_SECONDS:
                    self._trigger(self.options[hover_idx])
                    return
            else:
                self._hover_idx   = hover_idx
                self._hover_start = now
        else:
            self._hover_idx   = None
            self._hover_start = None

        # Dwell Volver
        if back_hover:
            if self._back_start is None:
                self._back_start = now
            elif now - self._back_start >= settings.BACK_DWELL_TIME:
                self.manager.go_to_main_menu()
                return
        else:
            self._back_start = None

        self._render(canvas, (cx, cy), positions, cursor, back_hover, now)

    # ------------------------------------------------------------------
    def _render(self, canvas, center, positions, cursor, back_hover, now):
        cx, cy = center

        if self.is_submenu and self.title:
            cv2.putText(canvas, self.title, (50, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.1, settings.COLOR_TEXT, 3, cv2.LINE_AA)

        for pos in positions:
            cv2.line(canvas, center, pos, settings.TEC_GRIS_CLARO, 2, cv2.LINE_AA)

        # Nodo central
        cv2.circle(canvas, center, settings.CENTER_NODE_RADIUS,
                   settings.COLOR_CENTER_NODE, -1, cv2.LINE_AA)
        label_c = "Menu" if not self.is_submenu else "TEC"
        _draw_text_centered(canvas, label_c, center,
                            font_scale=1.0, color=settings.COLOR_TEXT_ON_DARK, thickness=2)

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

            if is_hover and self._hover_start is not None:
                progress = min(1.0, (now - self._hover_start) / settings.DWELL_TIME_SECONDS)
                _draw_dwell_ring(canvas, pos, self.node_r, progress)

            label = opt.get("label", opt.get("id", ""))
            _draw_text_centered(canvas, label, (pos[0], pos[1] + self.node_r + 26),
                                font_scale=0.55, color=settings.COLOR_TEXT, thickness=1)

        # Botón Volver
        if self.is_submenu:
            bx, by = settings.BACK_BUTTON_POS
            br = settings.BACK_BUTTON_RADIUS
            color = settings.COLOR_AREA_NODE_HOVER if back_hover else settings.COLOR_AREA_NODE
            cv2.circle(canvas, (bx, by), br, color, -1, cv2.LINE_AA)
            cv2.circle(canvas, (bx, by), br, settings.COLOR_CENTER_NODE, 2, cv2.LINE_AA)
            _draw_text_centered(canvas, "Volver", (bx, by),
                                font_scale=0.55, color=settings.COLOR_TEXT, thickness=1)
            if back_hover and self._back_start is not None:
                p = min(1.0, (now - self._back_start) / settings.BACK_DWELL_TIME)
                _draw_dwell_ring(canvas, (bx, by), br, p)

        # Cursor
        if cursor is not None:
            cv2.circle(canvas, cursor, settings.CURSOR_RADIUS,
                       settings.COLOR_CURSOR, -1, cv2.LINE_AA)
            cv2.circle(canvas, cursor, settings.CURSOR_RADIUS + 3,
                       settings.TEC_BLANCO, 2, cv2.LINE_AA)

    # ------------------------------------------------------------------
    def _trigger(self, opt):
        action = opt.get("action")
        if action == "play_video":
            self.manager.go_to_video(opt["video"], return_to_submenu=self.is_submenu)
        elif action == "open_submenu":
            sub_id  = opt.get("id")
            options = content.SUBMENUS.get(sub_id, [])
            self.manager.go_to_submenu(options, title=opt.get("label", ""))
        elif action == "open_demo_menu":
            self.manager.go_to_demo_menu()


# ===========================================================================
# DemoMenuState  (grid táctil — 6 demos, layout configurable en settings)
# ===========================================================================

class DemoMenuState(BaseState):
    """
    Muestra las demos en un grid de botones rectangulares.
    Al hacer dwell sobre uno, escribe state.json y registra el acceso,
    luego cierra la app para que el watchdog lance la demo.
    """

    def __init__(self, manager):
        super().__init__(manager)
        self.demos        = content.DEMO_OPTIONS
        self._hover_idx:   Optional[int]   = None
        self._hover_start: Optional[float] = None
        self._back_start:  Optional[float] = None
        self._last_active = time.time()
        self._confirmed_idx: Optional[int] = None   # índice en pantalla de confirmación
        self._confirm_start: Optional[float] = None

        # Pre-calcular rectángulos de botones
        self._rects = self._compute_rects()

    # ------------------------------------------------------------------
    def _compute_rects(self):
        """Devuelve lista de (x1, y1, x2, y2) para cada botón."""
        cols    = settings.DEMO_GRID_COLS
        bw      = settings.DEMO_BUTTON_W
        bh      = settings.DEMO_BUTTON_H
        gap     = settings.DEMO_BUTTON_GAP
        top     = settings.DEMO_GRID_TOP
        n       = len(self.demos)
        rows    = math.ceil(n / cols)

        # Centrar el grid horizontalmente
        total_w = cols * bw + (cols - 1) * gap
        x0 = (settings.WINDOW_WIDTH - total_w) // 2

        rects = []
        for idx in range(n):
            row = idx // cols
            col = idx % cols
            x1 = x0 + col * (bw + gap)
            y1 = top + row * (bh + gap)
            rects.append((x1, y1, x1 + bw, y1 + bh))
        return rects

    # ------------------------------------------------------------------
    def update_and_render(self, canvas, hands_info: List[HandInfo]):
        now = time.time()

        raw_cursor = (hands_info[0].cursor_point
                      if hands_info and len(hands_info) == 1 else None)
        cursor = self.manager.smoother.update(raw_cursor)

        if cursor is not None:
            self._last_active = now
        elif now - self._last_active > settings.IDLE_TIMEOUT_SECONDS:
            self.manager.go_to_idle()
            return

        # Hover sobre botones
        hover_idx = None
        if cursor is not None:
            for i, (x1, y1, x2, y2) in enumerate(self._rects):
                if x1 <= cursor[0] <= x2 and y1 <= cursor[1] <= y2:
                    hover_idx = i
                    break

        # Hover sobre Volver
        bx, by = settings.BACK_BUTTON_POS
        br     = settings.BACK_BUTTON_RADIUS
        back_hover = (cursor is not None and _hypot(cursor, (bx, by)) < br)

        # Dwell sobre demo
        if hover_idx is not None:
            if self._hover_idx == hover_idx:
                elapsed = now - self._hover_start
                if elapsed >= settings.DWELL_TIME_SECONDS:
                    self._launch_demo(hover_idx)
                    return
            else:
                self._hover_idx   = hover_idx
                self._hover_start = now
        else:
            self._hover_idx   = None
            self._hover_start = None

        # Dwell sobre Volver
        if back_hover:
            if self._back_start is None:
                self._back_start = now
            elif now - self._back_start >= settings.BACK_DWELL_TIME:
                self.manager.go_to_main_menu()
                return
        else:
            self._back_start = None

        self._render(canvas, cursor, hover_idx, back_hover, now)

    # ------------------------------------------------------------------
    def _render(self, canvas, cursor, hover_idx, back_hover, now):
        h, w = canvas.shape[:2]

        # Título
        cv2.putText(canvas, "Demos Interactivos - IA",
                    (50, 80), cv2.FONT_HERSHEY_SIMPLEX,
                    1.4, settings.COLOR_TEXT, 3, cv2.LINE_AA)
        cv2.putText(canvas, "Levante su dedo sobre una demo para seleccionarla",
                    (50, 130), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, settings.TEC_GRIS, 2, cv2.LINE_AA)

        # Botones del grid
        for i, (x1, y1, x2, y2) in enumerate(self._rects):
            demo      = self.demos[i]
            is_hover  = (hover_idx == i)
            bcolor    = demo.get("color", settings.COLOR_AREA_NODE)
            fill      = settings.COLOR_AREA_NODE_HOVER if is_hover else bcolor

            # Fondo del botón
            cv2.rectangle(canvas, (x1, y1), (x2, y2), fill, -1)
            # Borde
            border_col = settings.TEC_ROJO if is_hover else settings.COLOR_CENTER_NODE
            cv2.rectangle(canvas, (x1, y1), (x2, y2), border_col, 3)

            # Etiqueta principal
            cx_b = (x1 + x2) // 2
            cy_b = (y1 + y2) // 2
            _draw_text_centered(canvas, demo["label"], (cx_b, cy_b - 20),
                                font_scale=1.1, color=settings.COLOR_TEXT_ON_DARK, thickness=3)
            # Descripción
            _draw_text_centered(canvas, demo.get("description", ""), (cx_b, cy_b + 28),
                                font_scale=0.6, color=settings.COLOR_TEXT_ON_DARK, thickness=1)

            # Anillo de progreso (dwell)
            if is_hover and self._hover_start is not None:
                progress = min(1.0, (now - self._hover_start) / settings.DWELL_TIME_SECONDS)
                ring_r   = min(settings.DEMO_BUTTON_W, settings.DEMO_BUTTON_H) // 2 - 10
                _draw_dwell_ring(canvas, (cx_b, cy_b), ring_r, progress)

        # Botón Volver
        bx, by = settings.BACK_BUTTON_POS
        br     = settings.BACK_BUTTON_RADIUS
        color  = settings.COLOR_AREA_NODE_HOVER if back_hover else settings.COLOR_AREA_NODE
        cv2.circle(canvas, (bx, by), br, color, -1, cv2.LINE_AA)
        cv2.circle(canvas, (bx, by), br, settings.COLOR_CENTER_NODE, 2, cv2.LINE_AA)
        _draw_text_centered(canvas, "Volver", (bx, by),
                            font_scale=0.55, color=settings.COLOR_TEXT, thickness=1)
        if back_hover and self._back_start is not None:
            p = min(1.0, (now - self._back_start) / settings.BACK_DWELL_TIME)
            _draw_dwell_ring(canvas, (bx, by), br, p)

        # Cursor
        if cursor is not None:
            cv2.circle(canvas, cursor, settings.CURSOR_RADIUS,
                       settings.COLOR_CURSOR, -1, cv2.LINE_AA)
            cv2.circle(canvas, cursor, settings.CURSOR_RADIUS + 3,
                       settings.TEC_BLANCO, 2, cv2.LINE_AA)

    # ------------------------------------------------------------------
    def _launch_demo(self, idx: int):
        """Registra el acceso, escribe state.json y señala al StateManager que cierre."""
        demo = self.demos[idx]

        # Ruta absoluta: ROOT_DIR / "demos/demo_N.py"
        script_abs = str(settings.ROOT_DIR / demo["script"])

        print(f"[demo_menu] Seleccionada: {demo['label']} → {script_abs}")
        _log_access(demo["id"], demo["label"], script_abs)

        # Escribir la ruta ABSOLUTA para que el watchdog la encuentre
        # independientemente del CWD desde donde fue lanzado.
        _write_state(script_abs)

        # Pedirle al StateManager que cierre la app principal
        self.manager.request_exit()


# ===========================================================================
# VideoState
# ===========================================================================

class VideoState(BaseState):
    def __init__(self, manager, video_filename: str,
                 return_to_submenu_options=None):
        super().__init__(manager)
        self.video_filename         = video_filename
        self.return_to_submenu_options = return_to_submenu_options
        self.video_path             = settings.VIDEOS_DIR / video_filename
        self.cap                    = cv2.VideoCapture(str(self.video_path))
        if not self.cap.isOpened():
            print(f"[video_state] No se pudo abrir: {self.video_path}")
        self._back_start: Optional[float] = None

    def update_and_render(self, canvas, hands_info: List[HandInfo]):
        now = time.time()
        h, w = canvas.shape[:2]

        ok, frame = self.cap.read()
        if not ok or frame is None:
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
        br     = settings.BACK_BUTTON_RADIUS
        back_hover = (cursor is not None and _hypot(cursor, (bx, by)) < br)

        if back_hover:
            if self._back_start is None:
                self._back_start = now
            elif now - self._back_start >= settings.BACK_DWELL_TIME:
                self._exit_video()
                return
        else:
            self._back_start = None

        color = settings.COLOR_AREA_NODE_HOVER if back_hover else settings.TEC_BLANCO
        cv2.circle(canvas, (bx, by), br, color, -1, cv2.LINE_AA)
        cv2.circle(canvas, (bx, by), br, settings.COLOR_CENTER_NODE, 2, cv2.LINE_AA)
        _draw_text_centered(canvas, "Menu", (bx, by),
                            font_scale=0.55, color=settings.COLOR_TEXT, thickness=1)
        if back_hover and self._back_start is not None:
            p = min(1.0, (now - self._back_start) / settings.BACK_DWELL_TIME)
            _draw_dwell_ring(canvas, (bx, by), br, p)

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
        self._current_submenu_options    = None
        self._current_submenu_title      = ""
        self._exit_requested             = False   # señal de cierre limpio
        self.go_to_idle()

    # ── Navegación ─────────────────────────────────────────────────────────

    def go_to_idle(self):
        self._current_submenu_options = None
        self._current_submenu_title   = ""
        self._state = IdleState(self)

    def go_to_main_menu(self):
        self._current_submenu_options = None
        self._current_submenu_title   = ""
        self._state = MenuState(self, options=content.MAIN_MENU_OPTIONS, is_submenu=False)

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
        self._state = VideoState(self, video_filename, return_to_submenu_options=opts)

    def go_to_demo_menu(self):
        self._state = DemoMenuState(self)

    def request_exit(self):
        """Señal para que el bucle principal en app.py salga limpiamente."""
        self._exit_requested = True

    @property
    def exit_requested(self) -> bool:
        return self._exit_requested

    # ── Bucle ──────────────────────────────────────────────────────────────

    def update_and_render(self, canvas, hands_info):
        if self._state is not None:
            self._state.update_and_render(canvas, hands_info)
