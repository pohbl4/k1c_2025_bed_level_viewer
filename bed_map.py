from __future__ import annotations

import ipaddress
import json
import math
import queue
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import Normalize, TwoSlopeNorm
import matplotlib.patheffects as pe
from matplotlib.figure import Figure
import numpy as np

API_PORT = 7125
API_PATH = "/printer/objects/query?bed_mesh"
BG = "#f3f6fa"
WHITE = "#ffffff"
INK = "#15213a"
MUTED = "#61718b"
BLUE = "#2563eb"
LINE = "#dee5ef"
FONT = "Segoe UI"

STRINGS = {
    "en": {
        "title": "Bed Map", "instruction_button": "Instructions", "language": "Language",
        "connection": "CONNECTION", "ip": "Printer IP address", "load": "Load map",
        "map_actions": "MAP TOOLS", "open": "Open JSON...", "save_png": "Save PNG...",
        "save_json": "Save JSON...", "points": "Show measured values",
        "legend_title": "HOW TO READ THE MAP",
        "legend": "Red = higher, blue = lower.\nThe front of the bed is at\nthe bottom of the image.",
        "read_only": "Read-only connection.\nRun calibration on the printer.",
        "minimum": "MINIMUM", "maximum": "MAXIMUM", "range": "RANGE",
        "initial_status": "Enter the printer IP address and select Load map.",
        "initial_source": "No data loaded", "initial_summary": "Read-only: no calibration or movement commands are sent.",
        "connecting": "Connecting to the printer...", "loaded": "Map loaded. Run Auto Leveling on the printer to create a new map.",
        "load_failed": "Could not load the map.", "loaded_file": "Map loaded from a file (no printer connection).",
        "source_active": "active map", "source_saved": "saved profile (not active)",
        "profile_none": "not specified",
        "source_info": "Source: {source}  |  Profile: {profile}  |  Measured grid: {cols} × {rows}",
        "edge_same": "{first} and {second} are approximately level",
        "edge_relative": "{first} is {direction} than {second} by an average of {amount:.3f} mm",
        "higher": "higher", "lower": "lower", "rear": "Rear edge", "front": "front edge",
        "right": "Right edge", "left": "left edge",
        "estimate": "Based on the outermost measured rows and columns.",
        "empty_title": "Your bed map will appear here",
        "empty_subtitle": "Connect to the printer or open a saved JSON file",
        "x_axis": "X, mm  ·  left to right", "y_axis": "Y, mm  ·  front to rear",
        "chart_title": "Bed height map  ·  range {delta:.3f} mm", "back_edge": "REAR OF BED",
        "front_edge": "FRONT OF BED", "color_label": "Height, mm", "mm": "mm",
        "invalid_address_title": "Invalid IP address", "error_title": "Unable to load map",
        "open_error": "Unable to open JSON", "save_error": "Unable to save file",
        "no_map_title": "No map loaded", "no_map": "Load a map from the printer or open a JSON file first.",
        "open_title": "Open saved bed map", "save_png_title": "Save map as an image",
        "save_json_title": "Save original measurements",
        "json_files": "JSON files", "all_files": "All files", "png_files": "PNG image",
        "file_saved": "Saved: {path}", "close": "Close",
        "instructions_title": "Instructions · How to create a bed map",
        "instructions_heading": "Complete guide: from calibration to bed map",
        "instructions_subtitle": "Creality K1C 2025 · stock firmware · no root access",
        "instructions_note": "This application only reads and visualizes an existing bed mesh. It does not calibrate the printer.",
        "error_empty_ip": "Enter the printer IP address (for example, 192.168.1.100).",
        "error_invalid_ip": "Enter a valid IPv4 or IPv6 address, without a port or URL.",
        "error_doc_type": "The JSON document must be an object, not an array.",
        "error_printer": "The printer returned an error: {details}",
        "error_result": "Unexpected printer response format.",
        "error_status": "The JSON response has no valid status object.",
        "error_missing_mesh": "No bed_mesh data found. Check the IP address and run Auto Leveling.",
        "error_not_active": "No active map or saved profiles found. Run Auto Leveling.",
        "error_matrix_values": "{name}: invalid numeric values.",
        "error_matrix_shape": "{name}: expected a rectangular numeric grid of at least 2 × 2.",
        "error_missing_bounds": "Missing or invalid mesh_min/mesh_max coordinates.",
        "error_invalid_bounds": "Invalid bed measurement boundaries.",
        "error_http": "HTTP {code}. Check the printer IP and API access on port 7125.",
        "error_network": "Could not connect. Check the IP, network and printer API (port 7125).\nDetails: {details}",
        "error_response_large": "Printer response exceeded 4 MB.",
        "error_not_json": "The response is not valid JSON. The printer API might be unavailable.",
        "error_unexpected": "Unexpected error: {details}",
    },
    "ru": {
        "title": "Карта стола", "instruction_button": "Инструкция", "language": "Язык",
        "connection": "ПОДКЛЮЧЕНИЕ", "ip": "IP-адрес принтера", "load": "Загрузить карту",
        "map_actions": "РАБОТА С КАРТОЙ", "open": "Открыть JSON...", "save_png": "Сохранить PNG...",
        "save_json": "Сохранить JSON...", "points": "Показывать значения точек",
        "legend_title": "КАК ЧИТАТЬ КАРТУ",
        "legend": "Красный — выше, синий — ниже.\nПередняя часть стола находится\nвнизу изображения.",
        "read_only": "Подключение только для чтения.\nКалибровку запускай на принтере.",
        "minimum": "МИНИМУМ", "maximum": "МАКСИМУМ", "range": "ПЕРЕПАД",
        "initial_status": "Введи IP-адрес принтера и нажми «Загрузить карту».",
        "initial_source": "Данные ещё не загружены", "initial_summary": "Только чтение: команды калибровки и движения не отправляются.",
        "connecting": "Подключаемся к принтеру...", "loaded": "Карта загружена. Для новой карты запусти Auto Leveling на принтере.",
        "load_failed": "Не удалось загрузить карту.", "loaded_file": "Карта загружена из файла (без подключения к принтеру).",
        "source_active": "активная карта", "source_saved": "сохранённый профиль (не активен)",
        "profile_none": "не указан",
        "source_info": "Источник: {source}  |  Профиль: {profile}  |  Сетка измерений: {cols} × {rows}",
        "edge_same": "{first} и {second} примерно на одном уровне",
        "edge_relative": "{first} {direction}, чем {second}, в среднем на {amount:.3f} мм",
        "higher": "выше", "lower": "ниже", "rear": "Задний край", "front": "передний край",
        "right": "Правый край", "left": "левый край",
        "estimate": "Оценка по крайним измеренным рядам и столбцам.",
        "empty_title": "Здесь появится карта стола",
        "empty_subtitle": "Подключись к принтеру или открой сохранённый JSON",
        "x_axis": "X, мм  ·  слева направо", "y_axis": "Y, мм  ·  спереди назад",
        "chart_title": "Карта высот стола  ·  перепад {delta:.3f} мм", "back_edge": "ЗАДНЯЯ ЧАСТЬ СТОЛА",
        "front_edge": "ПЕРЕДНЯЯ ЧАСТЬ СТОЛА", "color_label": "Высота, мм", "mm": "мм",
        "invalid_address_title": "Неверный IP-адрес", "error_title": "Не удалось загрузить карту",
        "open_error": "Не удалось открыть JSON", "save_error": "Ошибка сохранения",
        "no_map_title": "Нет карты", "no_map": "Сначала загрузи карту принтера или открой JSON.",
        "open_title": "Открыть сохранённую карту", "save_png_title": "Сохранить карту как изображение",
        "save_json_title": "Сохранить исходные измерения",
        "json_files": "JSON-файлы", "all_files": "Все файлы", "png_files": "Изображение PNG",
        "file_saved": "Сохранено: {path}", "close": "Закрыть",
        "instructions_title": "Инструкция · Как создать карту стола",
        "instructions_heading": "Полная инструкция: от калибровки до карты стола",
        "instructions_subtitle": "Creality K1C 2025 · штатная прошивка · без root-доступа",
        "instructions_note": "Приложение только считывает и показывает готовую карту. Само выравнивание оно не запускает.",
        "error_empty_ip": "Введи IP-адрес принтера (например, 192.168.0.0).",
        "error_invalid_ip": "Введи корректный адрес IPv4 или IPv6 — без порта и ссылки.",
        "error_doc_type": "JSON должен быть объектом, а не массивом.",
        "error_printer": "Принтер вернул ошибку: {details}",
        "error_result": "Неожиданный формат ответа принтера.",
        "error_status": "В JSON нет корректного объекта status.",
        "error_missing_mesh": "Не найдена карта bed_mesh. Проверь IP и выполни Auto Leveling.",
        "error_not_active": "Нет активной карты или сохранённого профиля. Выполни Auto Leveling.",
        "error_matrix_values": "{name}: некорректные числовые значения.",
        "error_matrix_shape": "{name}: нужна прямоугольная таблица чисел не менее 2 × 2.",
        "error_missing_bounds": "Отсутствуют или неверны координаты mesh_min/mesh_max.",
        "error_invalid_bounds": "Некорректные границы измерения стола.",
        "error_http": "Ошибка HTTP {code}. Проверь IP и доступность API на порту 7125.",
        "error_network": "Не удалось подключиться. Проверь IP, сеть и API принтера (порт 7125).\nПодробности: {details}",
        "error_response_large": "Ответ принтера больше 4 МБ.",
        "error_not_json": "Ответ не является корректным JSON. Возможно, API принтера недоступен.",
        "error_unexpected": "Неожиданная ошибка: {details}",
    },
}

INSTRUCTIONS = {
    "en": [
        ("Preparation after printing", [
            "1. Wait until printing is finished. Remove the printed part. Let the bed cool to around 35–40 °C before removing the PEI sheet.",
            "2. Remove the PEI sheet. Check both sides of the sheet and the magnetic base for debris or pieces of filament. Reinstall the sheet flat and fully seated.",
            "3. Inspect the nozzle for stuck-on plastic that could distort probing.",
            "4. Do not adjust the Z screws, timing belt or Z-offset before the baseline measurement.",
        ]),
        ("Preheating and auto leveling", [
            "5. Heat the bed to 60 °C for about 10 minutes. Use the same preparation and temperature when comparing repeated measurements.",
            "6. On the printer screen open Settings → Self-check (or System → Self-check) → Auto Leveling. Menu names can differ by firmware version.",
            "7. Run the bed leveling routine and let it finish. Input Shaping is not required for this bed check.",
            "8. If the printer changes the bed temperature automatically, do not interrupt it. Record the actual measurement conditions. Keep the printer on until the map is retrieved.",
        ]),
        ("Connecting the application", [
            "9. Make sure the computer and the K1C are on the same local network.",
            "10. Find the printer IP in its network settings. An example address is 192.168.1.100.",
            "11. Type only the IP address into the application.",
            "12. Select Load map. The app reads http://PRINTER_IP:7125/printer/objects/query?bed_mesh. It never sends movement, leveling or G-code commands.",
            "13. The rear of the bed is at the top, the front is at the bottom, and X increases from left to right. Red means higher, blue means lower.",
            "14. The minimum, maximum, and range use real measured probe points (probed_matrix); smooth coloring uses mesh_matrix.",
        ]),
        ("Troubleshooting", [
            "Cannot connect: verify the printer IP, local network access and that the firmware exposes its API on port 7125.",
            "HTTP error or non-JSON response: the API may be unavailable on this firmware or not accessible on the network.",
            "Map did not change: confirm that a fresh Auto Leveling procedure completed and updated the active or saved profile.",
        ]),
    ],
    "ru": [
        ("Подготовка после печати", [
            "1. Дождись завершения печати, сними модель. Перед снятием PEI-пластины дай столу остыть примерно до 35–40 °C.",
            "2. Сними пластину. Убери мусор и остатки пластика с обратной стороны пластины и магнитной основы. Установи пластину ровно и до упора.",
            "3. Осмотри сопло. Налипший пластик может исказить измерения.",
            "4. До первого контрольного измерения не трогай винты Z, приводной ремень и Z-offset.",
        ]),
        ("Прогрев и автовыравнивание", [
            "5. Прогрей стол до 60 °C около 10 минут. Для сравнения повторных измерений используй одинаковые условия.",
            "6. На экране K1C открой «Настройки → Самодиагностика» (или «Система → Самодиагностика») → «Автовыравнивание / Auto Leveling». Названия могут отличаться.",
            "7. Запусти калибровку стола и дождись её завершения. Input Shaping для этой проверки не требуется.",
            "8. Если принтер сам меняет температуру стола, не прерывай процедуру. Запиши фактические условия измерения. Не выключай принтер до получения карты.",
        ]),
        ("Подключение приложения", [
            "9. Убедись, что компьютер и K1C находятся в одной локальной сети.",
            "10. В настройках сети принтера найди его IP-адрес, например 192.168.0.0.",
            "11. Введи в приложение только IP-адрес.",
            "12. Нажми «Загрузить карту». Приложение читает адрес http://IP_ПРИНТЕРА:7125/printer/objects/query?bed_mesh и не отправляет принтеру команд движения или калибровки.",
            "13. Задняя часть стола на изображении сверху, передняя снизу, X увеличивается слева направо. Красный — выше, синий — ниже.",
            "14. Минимум, максимум и перепад рассчитываются по измеренным точкам probed_matrix, а плавная цветная карта — по mesh_matrix.",
        ]),
        ("Решение возможных проблем", [
            "Нет связи: проверь IP принтера, локальную сеть и доступность API прошивки на порту 7125.",
            "Ошибка HTTP или неверный JSON: в этой прошивке API может быть недоступен или заблокирован сетью.",
            "Карта не меняется: убедись, что повторное Auto Leveling действительно завершилось и обновило профиль.",
        ]),
    ],
}


class MeshError(ValueError):
    def __init__(self, key: str, **params: object) -> None:
        self.key, self.params = key, params
        super().__init__(STRINGS["en"].get(key, key).format(**params))


@dataclass
class MeshData:
    probed: np.ndarray
    interpolated: np.ndarray
    min_xy: tuple[float, float]
    max_xy: tuple[float, float]
    profile: str
    source_kind: str
    raw: dict

    @property
    def min_z(self) -> float:
        return float(np.min(self.probed))

    @property
    def max_z(self) -> float:
        return float(np.max(self.probed))

    @property
    def delta(self) -> float:
        return self.max_z - self.min_z

    @property
    def front_back(self) -> float:
        return float(self.probed[-1].mean() - self.probed[0].mean())

    @property
    def left_right(self) -> float:
        return float(self.probed[:, -1].mean() - self.probed[:, 0].mean())


def _as_matrix(value: object, name: str) -> np.ndarray:
    try:
        arr = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise MeshError("error_matrix_values", name=name) from exc
    if arr.ndim != 2 or min(arr.shape) < 2 or not np.all(np.isfinite(arr)):
        raise MeshError("error_matrix_shape", name=name)
    return arr


def parse_mesh(document: dict) -> MeshData:
    """Parse a Moonraker response or a saved bed mesh profile."""
    if not isinstance(document, dict):
        raise MeshError("error_doc_type")
    if "error" in document:
        raise MeshError("error_printer", details=str(document["error"]))
    result = document.get("result", document)
    if not isinstance(result, dict):
        raise MeshError("error_result")
    status = result.get("status", result)
    if not isinstance(status, dict):
        raise MeshError("error_status")
    obj = status.get("bed_mesh", status)
    if not isinstance(obj, dict) or not any(k in obj for k in ("probed_matrix", "profiles", "mesh_matrix")):
        raise MeshError("error_missing_mesh")

    raw_probe = obj.get("probed_matrix")

    try:
        _as_matrix(raw_probe, "probed_matrix")
        is_active = True
    except MeshError:
        is_active = False
    profile = str(obj.get("profile_name") or "")
    xy_min, xy_max = obj.get("mesh_min"), obj.get("mesh_max")
    if not is_active:
        profiles = obj.get("profiles") or {}
        if not isinstance(profiles, dict) or not profiles:
            raise MeshError("error_not_active")
        profile = "default" if "default" in profiles else next(iter(profiles))
        saved = profiles[profile]
        if not isinstance(saved, dict):
            raise MeshError("error_missing_mesh")
        raw_probe = saved.get("points")
        params = saved.get("mesh_params") or {}
        xy_min = [params.get("min_x"), params.get("min_y")]
        xy_max = [params.get("max_x"), params.get("max_y")]
        raw_interp = raw_probe
        source_kind = "source_saved"
    else:
        raw_interp = obj.get("mesh_matrix")

        try:
            _as_matrix(raw_interp, "mesh_matrix")
        except MeshError:
            raw_interp = raw_probe
        source_kind = "source_active"

    probed = _as_matrix(raw_probe, "probed_matrix")
    interpolated = _as_matrix(raw_interp, "mesh_matrix")
    try:
        a = (float(xy_min[0]), float(xy_min[1]))
        b = (float(xy_max[0]), float(xy_max[1]))
    except (ValueError, TypeError, IndexError) as exc:
        raise MeshError("error_missing_bounds") from exc
    if not all(math.isfinite(v) for v in (*a, *b)) or b[0] <= a[0] or b[1] <= a[1]:
        raise MeshError("error_invalid_bounds")
    return MeshData(probed, interpolated, a, b, profile, source_kind, document)


def parse_address(value: str) -> str:
    """Accept ONLY an IP address. The API port and endpoint are fixed."""
    value = value.strip()
    if not value:
        raise MeshError("error_empty_ip")
    try:
        address = ipaddress.ip_address(value)
    except ValueError as exc:
        raise MeshError("error_invalid_ip") from exc
    host = f"[{address.compressed}]" if address.version == 6 else str(address)
    return f"http://{host}:{API_PORT}{API_PATH}"


def download_mesh(url: str) -> dict:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "Bed-Map/2.0"})
    try:
        with urlopen(request, timeout=8) as response:
            payload = response.read(4 * 1024 * 1024 + 1)
            if len(payload) > 4 * 1024 * 1024:
                raise MeshError("error_response_large")
    except HTTPError as exc:
        raise MeshError("error_http", code=exc.code) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise MeshError("error_network", details=str(exc)) from exc
    try:
        data = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MeshError("error_not_json") from exc
    return data


class BedMapApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.language = "en"
        self.language_label = tk.StringVar(value="English")
        self.ip = tk.StringVar()
        self.labels_on = tk.BooleanVar(value=True)
        self.mesh: MeshData | None = None
        self.actions: queue.Queue[tuple[str, object]] = queue.Queue()
        self.busy = False
        self.status_key = "initial_status"
        self.status_params: dict = {}
        self.status = tk.StringVar()
        self.source = tk.StringVar()
        self.summary = tk.StringVar()
        self.translatable: list[tuple[tk.Widget, str]] = []
        self.metric_headers: list[tk.Label] = []
        self.metric_labels: list[tk.Label] = []
        self.instruction_window: tk.Toplevel | None = None
        self.instruction_body: tk.Text | None = None
        self.instruction_title_label: tk.Label | None = None
        self.instruction_subtitle_label: tk.Label | None = None
        self.instruction_close_btn: ttk.Button | None = None
        self.root.geometry("1210x830")
        self.root.minsize(950, 660)
        self.root.configure(bg=BG)
        self.root.option_add("*Font", (FONT, 10))
        self._make_style()
        self._make_ui()
        self._refresh_language()
        self.root.after(100, self._poll)

    def tr(self, key: str, **params: object) -> str:
        return STRINGS[self.language][key].format(**params)

    def localized_error(self, err: Exception) -> str:
        if isinstance(err, MeshError):
            return self.tr(err.key, **err.params)
        return self.tr("error_unexpected", details=str(err))

    def _make_style(self) -> None:
        s = ttk.Style(self.root)
        s.theme_use("clam")
        s.configure("Primary.TButton", font=(FONT, 11, "bold"), foreground="white", background=BLUE,
                    borderwidth=0, padding=(12, 12))
        s.map("Primary.TButton", background=[("active", "#1d4ed8"), ("disabled", "#a7bfe9")])
        s.configure("Secondary.TButton", font=(FONT, 10), foreground=INK, background="#e9eff8",
                    borderwidth=0, padding=(10, 11))
        s.map("Secondary.TButton", background=[("active", "#d9e5f6"), ("disabled", "#f0f3f7")])
        s.configure("Input.TEntry", padding=8, fieldbackground="white", foreground=INK)
        s.configure("Options.TCheckbutton", background=WHITE, foreground=INK, font=(FONT, 10))
        s.configure("Language.TCombobox", padding=5, font=(FONT, 10))

    def _register(self, widget: tk.Widget, key: str) -> tk.Widget:
        self.translatable.append((widget, key))
        return widget

    def _label(self, parent: tk.Widget, key: str, size=10, bold=False, color=INK, **kwargs) -> tk.Label:
        w = tk.Label(parent, font=(FONT, size, "bold" if bold else "normal"),
                     fg=color, bg=WHITE, anchor="w", **kwargs)
        self._register(w, key)
        return w

    def _button(self, parent: tk.Widget, key: str, command, primary=False) -> ttk.Button:
        w = ttk.Button(parent, style="Primary.TButton" if primary else "Secondary.TButton", command=command)
        self._register(w, key)
        return w

    def _make_ui(self) -> None:
        header = tk.Frame(self.root, bg=WHITE, height=77, highlightthickness=1, highlightbackground=LINE)
        header.pack(fill="x")
        header.pack_propagate(False)
        self._label(header, "title", size=17, bold=True).pack(side="left", padx=25)
        language_box = ttk.Combobox(header, textvariable=self.language_label, state="readonly",
                                    values=("English", "Русский"), width=11, style="Language.TCombobox")
        language_box.pack(side="right", padx=(4, 22), pady=16)
        language_box.bind("<<ComboboxSelected>>", self._language_changed)
        self._button(header, "instruction_button", self.show_instructions).pack(side="right", padx=(0, 12), pady=15)

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=15)
        sidebar = tk.Frame(body, bg=WHITE, width=310, highlightbackground=LINE, highlightthickness=1)
        sidebar.pack(side="left", fill="y", padx=(0, 14))
        sidebar.pack_propagate(False)
        main = tk.Frame(body, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        self._label(sidebar, "connection", 11, True).pack(anchor="w", padx=20, pady=(24, 20))
        self._label(sidebar, "ip", 10, True).pack(anchor="w", padx=20)
        self.ip_entry = ttk.Entry(sidebar, textvariable=self.ip, style="Input.TEntry", font=(FONT, 12))
        self.ip_entry.pack(fill="x", padx=20, pady=(7, 16))
        self.ip_entry.bind("<Return>", lambda _e: self.connect())
        self.load_btn = self._button(sidebar, "load", self.connect, primary=True)
        self.load_btn.pack(fill="x", padx=20, pady=(0, 20))
        tk.Frame(sidebar, bg=LINE, height=1).pack(fill="x", padx=20)
        self._label(sidebar, "map_actions", 10, True).pack(anchor="w", padx=20, pady=(20, 12))
        self._button(sidebar, "open", self.open_json).pack(fill="x", padx=20, pady=(0, 8))
        self._button(sidebar, "save_png", self.save_png).pack(fill="x", padx=20, pady=(0, 8))
        self._button(sidebar, "save_json", self.save_json).pack(fill="x", padx=20, pady=(0, 8))
        points_check = ttk.Checkbutton(sidebar, style="Options.TCheckbutton", variable=self.labels_on,
                                       command=self._draw)
        self._register(points_check, "points")
        points_check.pack(anchor="w", padx=20, pady=(9, 20))
        tk.Frame(sidebar, bg=LINE, height=1).pack(fill="x", padx=20)
        self._label(sidebar, "legend_title", 10, True).pack(anchor="w", padx=20, pady=(20, 10))
        self._label(sidebar, "legend", color=MUTED, justify="left").pack(anchor="w", padx=20)
        self._label(sidebar, "read_only", size=9, color=MUTED, justify="left").pack(
            side="bottom", anchor="w", padx=20, pady=22)

        metrics = tk.Frame(main, bg=BG)
        metrics.pack(fill="x", pady=(0, 12))
        for i, key in enumerate(("minimum", "maximum", "range")):
            frame = tk.Frame(metrics, bg=WHITE, highlightthickness=1, highlightbackground=LINE)
            frame.pack(side="left", fill="x", expand=True, padx=(0, 10 if i < 2 else 0))
            lab = tk.Label(frame, bg=WHITE, fg=MUTED, font=(FONT, 9, "bold"))
            lab.pack(anchor="w", padx=16, pady=(13, 1))
            self._register(lab, key)
            self.metric_headers.append(lab)
            val = tk.Label(frame, text="—", bg=WHITE, fg=INK, font=(FONT, 21, "bold"))
            val.pack(anchor="w", padx=16, pady=(0, 12))
            self.metric_labels.append(val)

        self.chart_frame = tk.Frame(main, bg=WHITE, highlightthickness=1, highlightbackground=LINE)
        self.chart_frame.pack(fill="both", expand=True)
        self.figure = Figure(figsize=(8.1, 6.5), dpi=100, facecolor=WHITE)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        footer = tk.Frame(main, bg=BG)
        footer.pack(fill="x", pady=(12, 0))
        tk.Label(footer, textvariable=self.source, bg=BG, fg=INK, font=(FONT, 10, "bold"),
                 anchor="w").pack(fill="x")
        tk.Label(footer, textvariable=self.summary, bg=BG, fg=MUTED, font=(FONT, 10),
                 anchor="w", wraplength=800, justify="left").pack(fill="x", pady=(3, 0))
        statusbar = tk.Frame(self.root, bg=WHITE, height=32)
        statusbar.pack(fill="x", side="bottom")
        tk.Label(statusbar, textvariable=self.status, bg=WHITE, fg=MUTED, anchor="w",
                 font=(FONT, 9)).pack(fill="x", padx=18, pady=8)
        self.ip_entry.focus_set()

    def _language_changed(self, _event=None) -> None:
        new_language = "ru" if self.language_label.get() == "Русский" else "en"
        if new_language != self.language:
            self.language = new_language
            self._refresh_language()

    def _set_status(self, key: str, **params: object) -> None:
        self.status_key, self.status_params = key, params
        self.status.set(self.tr(key, **params))

    def _refresh_language(self) -> None:
        self.root.title(self.tr("title"))
        for widget, key in self.translatable:
            widget.configure(text=self.tr(key))
        self.status.set(self.tr(self.status_key, **self.status_params))
        if self.mesh is None:
            self.source.set(self.tr("initial_source"))
            self.summary.set(self.tr("initial_summary"))
        else:
            self._update_stats()
        self._draw()
        self._refresh_instructions()

    def connect(self) -> None:
        if self.busy:
            return
        try:
            url = parse_address(self.ip.get())
        except MeshError as exc:
            messagebox.showerror(self.tr("invalid_address_title"), self.localized_error(exc), parent=self.root)
            return
        self.busy = True
        self.load_btn.state(["disabled"])
        self._set_status("connecting")

        def work() -> None:
            try:
                self.actions.put(("success", parse_mesh(download_mesh(url))))
            except Exception as exc:
                self.actions.put(("error", exc))
        threading.Thread(target=work, daemon=True).start()

    def _poll(self) -> None:
        try:
            while True:
                kind, result = self.actions.get_nowait()
                self.busy = False
                self.load_btn.state(["!disabled"])
                if kind == "success":
                    self._load_data(result)
                    self._set_status("loaded")
                else:
                    self._set_status("load_failed")
                    messagebox.showerror(self.tr("error_title"), self.localized_error(result), parent=self.root)
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _load_data(self, data: MeshData) -> None:
        self.mesh = data
        self._update_stats()
        self._draw()

    def _update_stats(self) -> None:
        if self.mesh is None:
            return
        mesh = self.mesh
        for idx, val in enumerate((mesh.min_z, mesh.max_z, mesh.delta)):
            self.metric_labels[idx].configure(text=(f"{val:+.3f}" if idx < 2 else f"{val:.3f}") + " " + self.tr("mm"))
        self.source.set(self.tr("source_info", source=self.tr(mesh.source_kind),
                                profile=mesh.profile or self.tr("profile_none"),
                                cols=mesh.probed.shape[1], rows=mesh.probed.shape[0]))
        def edge_desc(delta: float, first: str, second: str) -> str:
            if abs(delta) < 0.015:
                return self.tr("edge_same", first=first, second=second)
            return self.tr("edge_relative", first=first, second=second,
                           direction=self.tr("higher" if delta > 0 else "lower"), amount=abs(delta))
        self.summary.set(edge_desc(mesh.front_back, self.tr("rear"), self.tr("front")) + "; " +
                         edge_desc(mesh.left_right, self.tr("right"), self.tr("left")) +
                         ".  " + self.tr("estimate"))

    def _draw(self) -> None:
        if not hasattr(self, "figure"):
            return
        fig = self.figure
        fig.clear()
        if self.mesh is None:
            ax = fig.add_axes([0.08, 0.1, 0.84, 0.79])
            ax.set_facecolor("#f7f9fc")
            ax.set_axis_off()
            ax.text(0.5, 0.56, self.tr("empty_title"), ha="center", va="center",
                    fontsize=19, weight="bold", color=INK, transform=ax.transAxes)
            ax.text(0.5, 0.47, self.tr("empty_subtitle"), ha="center", va="center",
                    fontsize=11, color=MUTED, transform=ax.transAxes)
            self.canvas.draw_idle()
            return

        mesh = self.mesh
        ax = fig.add_axes([0.15, 0.18, 0.64, 0.66])
        ax.set_facecolor("#f7f9fc")
        minx, miny = mesh.min_xy
        maxx, maxy = mesh.max_xy
        lo = min(mesh.min_z, float(mesh.interpolated.min()))
        hi = max(mesh.max_z, float(mesh.interpolated.max()))
        if hi - lo < 0.001:
            lo -= 0.01
            hi += 0.01
        norm = TwoSlopeNorm(vmin=lo, vcenter=0, vmax=hi) if lo < 0 < hi else Normalize(vmin=lo, vmax=hi)
        img = ax.imshow(mesh.interpolated, extent=(minx, maxx, miny, maxy),
                        origin="lower", aspect="equal", cmap="RdYlBu_r",
                        interpolation="bilinear", norm=norm)
        xs = np.linspace(minx, maxx, mesh.probed.shape[1])
        ys = np.linspace(miny, maxy, mesh.probed.shape[0])
        if self.labels_on.get() and mesh.probed.size <= 225:
            for j, y in enumerate(ys):
                for i, x in enumerate(xs):
                    z = float(mesh.probed[j, i])
                    color = "white" if norm(z) < 0.19 or norm(z) > 0.81 else "#162335"
                    ax.text(x, y, f"{z:+.2f}", fontsize=8.3, color=color,
                            ha="center", va="center", fontweight="bold",
                            path_effects=[pe.withStroke(linewidth=1.6,
                                          foreground="#263248" if color == "white" else "#ffffff")])
        else:
            xx, yy = np.meshgrid(xs, ys)
            ax.scatter(xx, yy, s=10, c="black", alpha=0.5)
        pad_x = (maxx - minx) * 0.075
        pad_y = (maxy - miny) * 0.075
        ax.set_xlim(minx - pad_x, maxx + pad_x)
        ax.set_ylim(miny - pad_y, maxy + pad_y)
        ax.set_xlabel(self.tr("x_axis"), color=INK, fontsize=10, labelpad=8)
        ax.set_ylabel(self.tr("y_axis"), color=INK, fontsize=10, labelpad=8)
        ax.tick_params(axis="both", colors=MUTED, labelsize=9)
        for spine in ax.spines.values():
            spine.set_color(LINE)
        fig.text(0.47, 0.958, self.tr("chart_title", delta=mesh.delta),
                 ha="center", fontsize=15, color=INK, weight="bold")
        fig.text(0.47, 0.895, self.tr("back_edge"), ha="center", fontsize=9, color=MUTED)
        fig.text(0.47, 0.068, self.tr("front_edge"), ha="center", fontsize=9, color=MUTED)
        cax = fig.add_axes([0.85, 0.25, 0.027, 0.55])
        cb = fig.colorbar(img, cax=cax)
        cb.set_label(self.tr("color_label"), fontsize=10, color=INK)
        cb.ax.tick_params(labelsize=9, colors=MUTED)
        cb.outline.set_edgecolor(LINE)
        self.canvas.draw_idle()

    def open_json(self) -> None:
        path = filedialog.askopenfilename(title=self.tr("open_title"),
                                           filetypes=[(self.tr("json_files"), "*.json"),
                                                      (self.tr("all_files"), "*.*")])
        if not path:
            return
        try:
            with open(path, encoding="utf-8-sig") as f:
                data = parse_mesh(json.load(f))
            self._load_data(data)
            self._set_status("loaded_file")
        except (OSError, json.JSONDecodeError, MeshError, ValueError) as exc:
            msg = self.localized_error(exc) if isinstance(exc, MeshError) else str(exc)
            messagebox.showerror(self.tr("open_error"), msg, parent=self.root)

    def save_png(self) -> None:
        if self.mesh is None:
            messagebox.showinfo(self.tr("no_map_title"), self.tr("no_map"), parent=self.root)
            return
        path = filedialog.asksaveasfilename(title=self.tr("save_png_title"),
                                            defaultextension=".png", initialfile="bed_map.png",
                                            filetypes=[(self.tr("png_files"), "*.png")])
        if not path:
            return
        try:
            self.figure.savefig(path, dpi=190, facecolor=WHITE)
            self._set_status("file_saved", path=path)
        except OSError as exc:
            messagebox.showerror(self.tr("save_error"), str(exc), parent=self.root)

    def save_json(self) -> None:
        if self.mesh is None:
            messagebox.showinfo(self.tr("no_map_title"), self.tr("no_map"), parent=self.root)
            return
        path = filedialog.asksaveasfilename(title=self.tr("save_json_title"),
                                            defaultextension=".json", initialfile="bed_map.json",
                                            filetypes=[(self.tr("json_files"), "*.json")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.mesh.raw, f, ensure_ascii=False, indent=2)
            self._set_status("file_saved", path=path)
        except OSError as exc:
            messagebox.showerror(self.tr("save_error"), str(exc), parent=self.root)

    def show_instructions(self) -> None:
        if self.instruction_window is not None and self.instruction_window.winfo_exists():
            self.instruction_window.lift()
            self.instruction_window.focus_set()
            return
        win = tk.Toplevel(self.root)
        self.instruction_window = win
        win.geometry("870x700")
        win.minsize(620, 440)
        win.configure(bg=WHITE)
        self.instruction_title_label = tk.Label(win, bg=WHITE, fg=INK, font=(FONT, 15, "bold"))
        self.instruction_title_label.pack(anchor="w", padx=20, pady=(20, 6))
        self.instruction_subtitle_label = tk.Label(win, bg=WHITE, fg=MUTED, font=(FONT, 10))
        self.instruction_subtitle_label.pack(anchor="w", padx=20, pady=(0, 14))
        frame = tk.Frame(win, bg=WHITE)
        frame.pack(fill="both", expand=True, padx=18)
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        text = tk.Text(frame, font=(FONT, 10), fg=INK, bg=WHITE, wrap="word",
                       padx=8, pady=8, bd=0, highlightthickness=0,
                       spacing1=4, spacing3=6, yscrollcommand=scrollbar.set)
        text.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=text.yview)
        text.tag_configure("heading", font=(FONT, 12, "bold"), foreground=BLUE,
                           spacing1=16, spacing3=6)
        text.tag_configure("note", font=(FONT, 10, "bold"), foreground=INK)
        self.instruction_body = text
        bottom = tk.Frame(win, bg=WHITE)
        bottom.pack(fill="x", padx=20, pady=16)
        self.instruction_close_btn = ttk.Button(bottom, style="Secondary.TButton", command=win.destroy)
        self.instruction_close_btn.pack(side="right")
        win.protocol("WM_DELETE_WINDOW", win.destroy)
        win.transient(self.root)
        self._refresh_instructions()
        win.focus_set()

    def _refresh_instructions(self) -> None:
        win = self.instruction_window
        if win is None or not win.winfo_exists():
            return
        win.title(self.tr("instructions_title"))
        self.instruction_title_label.configure(text=self.tr("instructions_heading"))
        self.instruction_subtitle_label.configure(text=self.tr("instructions_subtitle"))
        self.instruction_close_btn.configure(text=self.tr("close"))
        body = self.instruction_body
        position = body.yview()[0]
        body.configure(state="normal")
        body.delete("1.0", "end")
        body.insert("end", self.tr("instructions_note") + "\n\n", "note")
        for title, paragraphs in INSTRUCTIONS[self.language]:
            body.insert("end", title + "\n", "heading")
            for para in paragraphs:
                body.insert("end", para + "\n\n")
        body.configure(state="disabled")
        body.yview_moveto(position)


def main() -> None:
    root = tk.Tk()
    BedMapApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
