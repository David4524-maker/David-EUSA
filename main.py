"""David EUSA - Consola lanzadora de apps web y juegos (interfaz de consola portátil)."""
from __future__ import annotations

import copy
import csv
import json
import logging
import os
import platform
import queue
import random
import re
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk
from urllib.parse import quote_plus, urlparse

# ----------------------------------------------------------------- Constantes
CONFIG_DIR = Path.home() / ".david_eusa"
CONFIG_FILE = CONFIG_DIR / "config.json"
BACKUP_DIR = CONFIG_DIR / "backups"
LOG_FILE = CONFIG_DIR / "david_eusa.log"
EPIC_MANIFESTS = Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "Epic/EpicGamesLauncher/Data/Manifests"
CATEGORIAS = ["Acción", "Aventura", "Arcade", "Estrategia", "Deportes",
              "Carreras", "Puzzle", "Sandbox", "Otros"]
IGNORAR_EXE = ("unins", "setup", "crash", "redist", "vc_", "dxsetup", "updater")

# Colores de la paleta de tu dibujo: verde 22B14C, azul 00A2E8, celeste 99D9EA, morado A349A4, rojo ED1C24
THEMES = {
    "Consola": dict(bg="#99d9ea", panel="#eaf8fc", fg="#000000", muted="#2f5663", accent="#ed1c24",
                    button="#a349a4", tabline="#a349a4", shell="#22b14c", desk="#ffffff", border="#00a2e8"),
    "Oscuro": dict(bg="#1a1a2e", panel="#16213e", fg="#ffffff", muted="#9aa0b4", accent="#e94560",
                   button="#0f3460", tabline="#e94560", shell="#2d2d44", desk="#0c0c14", border="#e94560"),
    "Claro": dict(bg="#f2f2f7", panel="#ffffff", fg="#1c1c1e", muted="#6b6b76", accent="#d6336c",
                  button="#4263eb", tabline="#4263eb", shell="#c9c9d6", desk="#ffffff", border="#4263eb"),
    "Neón": dict(bg="#050505", panel="#0d0d0d", fg="#39ff14", muted="#2aa80f", accent="#ff00e6",
                 button="#003b2f", tabline="#39ff14", shell="#101010", desk="#000000", border="#ff00e6"),
}

# (clave, texto, icono, ancho relativo) en el orden de tu dibujo
TABS = [("juegos", "JUEGOS", "🎮", 30), ("util", "UTILIDAD", "👜", 30), ("web", "APPS WEB", "🌐", 40),
        ("inicio", "INICIO", "🏠", 26), ("notas", "NOTAS", "📄", 26)]

PISTAS = {"joy": "Joystick: buscar juego (Ctrl+F)", "gris": "Botón gris: pantalla completa (F11)",
          "dp_up": "▲ Subir en la lista de juegos", "dp_down": "▼ Bajar en la lista de juegos",
          "dp_left": "◀ Pestaña anterior", "dp_right": "▶ Pestaña siguiente",
          "btn_A": "A: jugar el juego seleccionado", "btn_B": "B: ir a Inicio",
          "btn_X": "X: juego aleatorio", "btn_Y": "Y: marcar / quitar favorito"}

CATALOG_V = 2
UI_V = 2

# (nombre, Steam AppID, categoría) -> se lanzan con steam://run/<AppID>
CATALOGO = [
    ("Counter-Strike 2", 730, "Acción"), ("Dota 2", 570, "Estrategia"),
    ("Team Fortress 2", 440, "Acción"), ("Portal", 400, "Puzzle"),
    ("Portal 2", 620, "Puzzle"), ("Half-Life 2", 220, "Acción"),
    ("Half-Life", 70, "Acción"), ("Left 4 Dead 2", 550, "Acción"),
    ("Left 4 Dead", 500, "Acción"), ("Terraria", 105600, "Sandbox"),
    ("Stardew Valley", 413150, "Sandbox"), ("Garry's Mod", 4000, "Sandbox"),
    ("Rust", 252490, "Sandbox"), ("ARK: Survival Evolved", 346110, "Aventura"),
    ("PUBG: Battlegrounds", 578080, "Acción"), ("Apex Legends", 1172470, "Acción"),
    ("Grand Theft Auto V", 271590, "Acción"), ("Cyberpunk 2077", 1091500, "Acción"),
    ("The Witcher 3", 292030, "Aventura"), ("Elden Ring", 1245620, "Acción"),
    ("Skyrim Special Edition", 489830, "Aventura"), ("Fallout 4", 377160, "Aventura"),
    ("Fallout: New Vegas", 22380, "Aventura"), ("Among Us", 945360, "Arcade"),
    ("Hollow Knight", 367520, "Aventura"), ("Cuphead", 268910, "Arcade"),
    ("Undertale", 391540, "Aventura"), ("Celeste", 504230, "Arcade"),
    ("Hades", 1145360, "Acción"), ("Dead Cells", 588650, "Acción"),
    ("Slay the Spire", 646570, "Estrategia"), ("Vampire Survivors", 1794680, "Arcade"),
    ("Valheim", 892970, "Sandbox"), ("Subnautica", 264710, "Aventura"),
    ("The Forest", 242760, "Aventura"), ("Sons of the Forest", 1326470, "Aventura"),
    ("Don't Starve Together", 322330, "Aventura"), ("Project Zomboid", 108600, "Aventura"),
    ("RimWorld", 294100, "Estrategia"), ("Factorio", 427520, "Estrategia"),
    ("Satisfactory", 526870, "Sandbox"), ("Cities: Skylines", 255710, "Estrategia"),
    ("Civilization VI", 289070, "Estrategia"), ("Civilization V", 8930, "Estrategia"),
    ("Age of Empires II: DE", 813780, "Estrategia"), ("Age of Empires IV", 1466860, "Estrategia"),
    ("Stellaris", 281990, "Estrategia"), ("Hearts of Iron IV", 394360, "Estrategia"),
    ("Crusader Kings III", 1158310, "Estrategia"), ("Euro Truck Simulator 2", 227300, "Carreras"),
    ("American Truck Simulator", 270880, "Carreras"), ("Assetto Corsa", 244210, "Carreras"),
    ("Forza Horizon 5", 1551360, "Carreras"), ("Mount & Blade II: Bannerlord", 261550, "Estrategia"),
    ("Baldur's Gate 3", 1086940, "Aventura"), ("Red Dead Redemption 2", 1174180, "Acción"),
    ("Destiny 2", 1085660, "Acción"), ("Path of Exile", 238960, "Acción"),
    ("Rainbow Six Siege", 359550, "Acción"), ("Helldivers 2", 553850, "Acción"),
    ("Palworld", 1623730, "Aventura"), ("Lethal Company", 1966720, "Acción"),
    ("It Takes Two", 1426210, "Aventura"), ("Kenshi", 233860, "Sandbox"),
    ("Stray", 1332010, "Aventura"), ("Conan Exiles", 440900, "Aventura"),
    ("Unturned", 304930, "Sandbox"), ("Dead by Daylight", 381210, "Acción"),
    ("Geometry Dash", 322170, "Arcade"), ("God of War", 1593500, "Acción"),
    ("Horizon Zero Dawn", 1151640, "Aventura"), ("Warframe", 230410, "Acción"),
    ("War Thunder", 236390, "Acción"), ("Sea of Thieves", 1172620, "Aventura"),
    ("NieR: Automata", 524220, "Acción"), ("Titanfall 2", 1237970, "Acción"),
    ("Planet Zoo", 703080, "Estrategia"), ("Planet Coaster", 493340, "Estrategia"),
    ("Total War: WARHAMMER III", 1142710, "Estrategia"), ("Borderlands 2", 49520, "Acción"),
    ("Borderlands 3", 729040, "Acción"), ("Risk of Rain 2", 632360, "Acción"),
    ("Dying Light", 239140, "Acción"), ("Dying Light 2", 534380, "Acción"),
    ("Resident Evil 2", 883710, "Acción"), ("Resident Evil 4", 2050650, "Acción"),
    ("Resident Evil 7", 418370, "Acción"), ("The Binding of Isaac: Rebirth", 250900, "Arcade"),
    ("Enter the Gungeon", 311690, "Arcade"), ("Hotline Miami", 219150, "Arcade"),
    ("Papers, Please", 239030, "Puzzle"), ("Baba Is You", 736260, "Puzzle"),
    ("The Witness", 210970, "Puzzle"), ("Human: Fall Flat", 477160, "Puzzle"),
    ("Fall Guys", 1097150, "Arcade"), ("Bloons TD 6", 960090, "Estrategia"),
    ("Plants vs. Zombies GOTY", 3590, "Estrategia"), ("Brawlhalla", 291550, "Arcade"),
    ("Spelunky 2", 418530, "Arcade"), ("Disco Elysium", 632470, "Aventura"),
    ("Ori and the Blind Forest", 387290, "Aventura"), ("Cult of the Lamb", 1313140, "Acción"),
    ("Core Keeper", 1621690, "Sandbox"), ("Phasmophobia", 739630, "Acción"),
    ("Overcooked! 2", 728880, "Arcade"), ("Raft", 648800, "Sandbox"),
    ("Grounded", 962130, "Aventura"), ("Hunt: Showdown", 594650, "Acción"),
    ("Payday 2", 218620, "Acción"), ("Deep Rock Galactic", 548430, "Acción"),
    ("Sekiro: Shadows Die Twice", 814380, "Acción"), ("Dark Souls III", 374320, "Acción"),
    ("Monster Hunter: World", 582010, "Acción"), ("Inscryption", 1092790, "Puzzle"),
][:99]

# (nombre, categoría) -> abren la búsqueda en la tienda de Epic hasta que sincronices los instalados
CATALOGO_EPIC = [
    ("Fortnite", "Acción"), ("Rocket League", "Deportes"), ("Genshin Impact", "Aventura"),
    ("Honkai: Star Rail", "Aventura"), ("Alan Wake 2", "Acción"), ("Control", "Acción"),
    ("Alan Wake Remastered", "Acción"), ("Borderlands: The Pre-Sequel", "Acción"),
    ("Tiny Tina's Wonderlands", "Acción"), ("Death Stranding", "Acción"),
    ("Metro Exodus", "Acción"), ("Subnautica: Below Zero", "Aventura"),
    ("Kingdom Come: Deliverance", "Aventura"), ("Assassin's Creed Valhalla", "Aventura"),
    ("Assassin's Creed Odyssey", "Aventura"), ("Far Cry 6", "Acción"), ("Watch Dogs 2", "Acción"),
    ("Batman: Arkham Knight", "Acción"), ("Batman: Arkham City", "Acción"),
    ("Mortal Kombat 11", "Acción"), ("Mortal Kombat 1", "Acción"), ("Hogwarts Legacy", "Aventura"),
    ("Star Wars Jedi: Fallen Order", "Aventura"), ("Star Wars Jedi: Survivor", "Aventura"),
    ("Star Wars: Squadrons", "Acción"), ("Remnant: From the Ashes", "Acción"),
    ("Remnant II", "Acción"), ("Ghostrunner", "Acción"), ("Outer Wilds", "Aventura"),
    ("Untitled Goose Game", "Puzzle"), ("Rogue Legacy 2", "Arcade"), ("Inside", "Puzzle"),
    ("Limbo", "Puzzle"), ("Astroneer", "Sandbox"), ("A Plague Tale: Innocence", "Aventura"),
    ("A Plague Tale: Requiem", "Aventura"), ("Wasteland 3", "Estrategia"),
    ("Pillars of Eternity", "Aventura"), ("Return to Monkey Island", "Aventura"),
    ("Tales from the Borderlands", "Aventura"), ("The Wolf Among Us", "Aventura"),
    ("The Walking Dead: Definitive Series", "Aventura"), ("Hitman 3", "Acción"),
    ("Saints Row", "Acción"), ("Shadow of the Tomb Raider", "Aventura"),
    ("Rise of the Tomb Raider", "Aventura"), ("Tomb Raider", "Aventura"),
    ("Lies of P", "Acción"), ("Sifu", "Acción"), ("Dauntless", "Acción"),
    ("Football Manager 2024", "Deportes"), ("Lords of the Fallen", "Acción"),
    ("Total War: Three Kingdoms", "Estrategia"), ("Total War: WARHAMMER II", "Estrategia"),
    ("Frostpunk", "Estrategia"), ("This War of Mine", "Estrategia"),
    ("Surviving Mars", "Estrategia"), ("Night in the Woods", "Aventura"),
    ("Overcooked!", "Arcade"), ("Superhot", "Acción"), ("Anno 1800", "Estrategia"),
    ("Moonlighter", "Arcade"), ("Oddworld: New 'n' Tasty", "Arcade"),
    ("Mafia: Definitive Edition", "Acción"), ("Mafia II: Definitive Edition", "Acción"),
    ("Mafia III: Definitive Edition", "Acción"), ("BioShock: The Collection", "Acción"),
    ("XCOM 2", "Estrategia"), ("XCOM: Enemy Unknown", "Estrategia"),
    ("Evil Genius 2", "Estrategia"), ("Phoenix Point", "Estrategia"),
    ("Kerbal Space Program", "Sandbox"), ("Tropico 6", "Estrategia"),
    ("Jurassic World Evolution 2", "Estrategia"), ("DiRT 5", "Carreras"),
    ("Wreckfest", "Carreras"), ("Hot Wheels Unleashed", "Carreras"),
    ("Pathfinder: Kingmaker", "Aventura"), ("Pathfinder: Wrath of the Righteous", "Aventura"),
    ("Divinity: Original Sin 2", "Aventura"), ("Gears Tactics", "Estrategia"),
    ("Crysis Remastered", "Acción"), ("Metro 2033 Redux", "Acción"),
    ("Metro: Last Light Redux", "Acción"), ("Death's Door", "Aventura"), ("Sable", "Aventura"),
    ("The Outer Worlds", "Aventura"), ("Kena: Bridge of Spirits", "Aventura"),
    ("Maneater", "Acción"), ("Rebel Galaxy", "Acción"), ("What Remains of Edith Finch", "Aventura"),
    ("Journey", "Aventura"), ("A Short Hike", "Aventura"), ("GRIS", "Aventura"),
    ("Hyper Light Drifter", "Acción"), ("Chivalry 2", "Acción"), ("Manifold Garden", "Puzzle"),
    ("Absolute Drift", "Carreras"), ("Ghostwire: Tokyo", "Acción"), ("Dead Island 2", "Acción"),
]


def url_epic(nombre: str) -> str:
    return f"https://store.epicgames.com/es-ES/browse?q={quote_plus(nombre)}&sortBy=relevancy&sortDir=DESC&count=40"


def _juego(nombre: str, ruta: str, cat: str, fav: bool = False) -> dict:
    return {"name": nombre, "path": ruta, "category": cat, "favorite": fav,
            "plays": 0, "last_played": "", "seconds": 0}


def anadir_catalogo(cfg: dict) -> int:
    """Añade los juegos de los catálogos (Steam + Epic) que falten. Devuelve cuántos añadió."""
    existentes = {g["name"] for g in cfg["games"]}
    nuevos = [_juego(n, f"steam://run/{i}", c) for n, i, c in CATALOGO if n not in existentes]
    nuevos += [_juego(n, url_epic(n), c) for n, c in CATALOGO_EPIC if n not in existentes]
    cfg["games"].extend(nuevos)
    return len(nuevos)


def _norm(texto: str) -> str:
    return re.sub(r"[^a-z0-9]", "", texto.lower())


def leer_epic_instalados() -> list[tuple[str, str]]:
    """Lee los manifiestos del Epic Games Launcher: [(nombre, uri de lanzamiento)]."""
    res = []
    if not EPIC_MANIFESTS.exists():
        return res
    for f in EPIC_MANIFESTS.glob("*.item"):
        try:
            d = json.loads(f.read_text("utf-8"))
        except Exception:
            continue
        nombre, app = d.get("DisplayName"), d.get("AppName")
        if not nombre or not app or d.get("bIsIncompleteInstall"):
            continue
        ns, cid = d.get("CatalogNamespace"), d.get("CatalogItemId")
        ident = f"{ns}%3A{cid}%3A{app}" if ns and cid else app
        res.append((nombre, f"com.epicgames.launcher://apps/{ident}?action=launch&silent=true"))
    return res


DEFAULT_CONFIG = {
    "geometry": None,
    "theme": "Consola",
    "accent": None,
    "confirm_exit": True,
    "new_window": False,
    "notes": "",
    "catalog_v": CATALOG_V,
    "ui_v": UI_V,
    "webapps": [
        {"name": "OSC-Browser", "url": "https://david4524-maker.github.io/OSC-Browser/"},
        {"name": "ezpack-ai", "url": "https://david4524-maker.github.io/ezpack-ai/"},
        {"name": "LibrePhoto", "url": "https://david4524-maker.github.io/LibrePhoto/"},
    ],
    "games": [_juego("Minecraft Bedrock", "minecraft:", "Sandbox", True)]
             + [_juego(n, f"steam://run/{i}", c) for n, i, c in CATALOGO]
             + [_juego(n, url_epic(n), c) for n, c in CATALOGO_EPIC],
}


# ------------------------------------------------------------------ Utilidades
def cargar_config() -> dict:
    """Carga la config, la fusiona con los valores por defecto y migra versiones antiguas."""
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if CONFIG_FILE.exists():
            guardado = json.loads(CONFIG_FILE.read_text("utf-8"))
            cfg.update(guardado)
            if guardado.get("catalog_v") != CATALOG_V:  # config antigua: añadir catálogos
                anadir_catalogo(cfg)
                cfg["catalog_v"] = CATALOG_V
            if guardado.get("ui_v") != UI_V:  # nueva interfaz de consola
                cfg.update(theme="Consola", accent=None, geometry=None, ui_v=UI_V)
    except Exception:
        logging.exception("No se pudo leer la configuración")
    return cfg


def guardar_config(cfg: dict) -> None:
    """Guarda la config de forma atómica (archivo temporal + reemplazo)."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), "utf-8")
    os.replace(tmp, CONFIG_FILE)


def hacer_backup(max_copias: int = 5) -> None:
    """Copia rotativa de la configuración."""
    if not CONFIG_FILE.exists():
        return
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(CONFIG_FILE, BACKUP_DIR / f"config_{datetime.now():%Y%m%d_%H%M%S}.json")
    for viejo in sorted(BACKUP_DIR.glob("config_*.json"))[:-max_copias]:
        viejo.unlink(missing_ok=True)


def abrir_con_sistema(destino: str) -> None:
    """Abre archivo, carpeta o URI con el programa del sistema (multiplataforma)."""
    if sys.platform.startswith("win"):
        os.startfile(destino)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", destino])
    else:
        subprocess.Popen(["xdg-open", destino])


def es_protocolo(ruta: str) -> bool:
    """True para steam://..., minecraft:, https://... (no para C:\\...)."""
    return bool(re.match(r"^[A-Za-z][A-Za-z0-9+.-]+:", ruta))


def normalizar_url(url: str) -> str | None:
    """Valida la URL; añade https:// si falta. Devuelve None si no es válida."""
    url = url.strip()
    if not url:
        return None
    if not re.match(r"^https?://", url):
        url = "https://" + url
    p = urlparse(url)
    return url if p.netloc and "." in p.netloc else None


def fmt_tiempo(seg: int) -> str:
    h, m = divmod(int(seg) // 60, 60)
    return f"{h} h {m:02d} min" if h else f"{m} min"


def aclarar(color: str, f: float = 0.18) -> str:
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    r, g, b = (int(c + (255 - c) * f) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def rect_redondo(c: tk.Canvas, x0, y0, x1, y1, r, **kw) -> int:
    pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1,
           x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
    return c.create_polygon(pts, smooth=True, **kw)


class Tooltip:
    """Globo de ayuda al pasar el ratón."""

    def __init__(self, widget: tk.Widget, texto: str) -> None:
        self.widget, self.texto, self.tip = widget, texto, None
        widget.bind("<Enter>", self.mostrar, add="+")
        widget.bind("<Leave>", self.ocultar, add="+")

    def mostrar(self, _=None) -> None:
        if self.tip:
            return
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.texto, bg="#ffffe0", fg="black",
                 relief="solid", borderwidth=1, padx=5, pady=2).pack()

    def ocultar(self, _=None) -> None:
        if self.tip:
            self.tip.destroy()
            self.tip = None


# ------------------------------------------------------------------ Aplicación
class App:
    def __init__(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                            format="%(asctime)s %(levelname)s %(message)s")
        self.cfg = cargar_config()
        hacer_backup()
        self.cola: queue.Queue = queue.Queue()
        self.sort_col, self.sort_rev = "name", False
        self.status_job = self.notes_job = None
        self.tab_actual = "inicio"

        self.root = tk.Tk()
        self.root.title("David EUSA")
        self.root.minsize(900, 640)
        self.root.report_callback_exception = self.error_global
        self._geometria_inicial()
        self.root.protocol("WM_DELETE_WINDOW", self.salir)

        # La consola: un lienzo con el cuerpo verde y, encima, la pantalla azul
        self.canvas = tk.Canvas(self.root, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.pantalla = tk.Frame(self.canvas, highlightthickness=0)
        self.canvas.bind("<Configure>", self.dibujar_consola)
        self._controles()
        self._atajos()

        self.var_busqueda = tk.StringVar()
        self.var_cat = tk.StringVar(value="Todas")
        self.var_fav = tk.BooleanVar(value=False)
        self.var_busqueda.trace_add("write", lambda *_: self.refrescar_juegos())

        self.construir_ui()
        self.tick()

    # ------------------------------------------------------------- Infra
    def _geometria_inicial(self) -> None:
        geo = self.cfg.get("geometry")
        if geo:
            self.root.geometry(geo)
        else:
            w, h = 1000, 710
            x = max(0, (self.root.winfo_screenwidth() - w) // 2)
            y = max(0, (self.root.winfo_screenheight() - h) // 2 - 20)
            self.root.geometry(f"{w}x{h}+{x}+{y}")

    def error_global(self, exc, val, tb) -> None:
        logging.error("Error no controlado", exc_info=(exc, val, tb))
        messagebox.showerror("Error inesperado", f"{val}\n\nDetalles en:\n{LOG_FILE}")

    def guardar(self) -> None:
        try:
            guardar_config(self.cfg)
        except Exception:
            logging.exception("No se pudo guardar")
            self.status("⚠ No se pudo guardar la configuración")

    @property
    def T(self) -> dict:
        t = dict(THEMES.get(self.cfg["theme"], THEMES["Consola"]))
        if self.cfg.get("accent"):
            t["accent"] = self.cfg["accent"]
        return t

    def status(self, msg: str) -> None:
        lbl = getattr(self, "lbl_status", None)
        if lbl is not None and lbl.winfo_exists():
            lbl.config(text=msg)
            if self.status_job:
                self.root.after_cancel(self.status_job)
            self.status_job = self.root.after(6000, self._status_listo)

    def _status_listo(self) -> None:
        lbl = getattr(self, "lbl_status", None)
        if lbl is not None and lbl.winfo_exists():
            lbl.config(text="Listo")

    def _atajos(self) -> None:
        r = self.root
        r.bind("<F11>", lambda e: self.pantalla_completa())
        r.bind("<Escape>", lambda e: r.attributes("-fullscreen", False))
        r.bind("<Control-q>", lambda e: self.salir())
        r.bind("<F5>", lambda e: self.refrescar_todo())
        r.bind("<Control-n>", lambda e: self.anadir_juego())
        r.bind("<Control-f>", lambda e: self.enfocar_busqueda())
        r.bind("<Control-Left>", lambda e: self.cambiar_tab(-1))
        r.bind("<Control-Right>", lambda e: self.cambiar_tab(1))
        for i, (clave, *_) in enumerate(TABS, 1):
            r.bind(f"<Control-Key-{i}>", lambda e, k=clave: self.mostrar_tab(k))

    def pantalla_completa(self) -> None:
        r = self.root
        r.attributes("-fullscreen", not r.attributes("-fullscreen"))

    # ------------------------------------------------------------- La consola (cuerpo y botones)
    def dibujar_consola(self, _=None) -> None:
        c, T = self.canvas, self.T
        W, H = c.winfo_width(), c.winfo_height()
        if W < 300 or H < 300:
            return
        u = min(W / 1000, H / 710)
        c.configure(bg=T["desk"])
        c.delete("shell")

        # Cuerpo verde y marco azul de la pantalla
        rect_redondo(c, .024 * W, .077 * H, .975 * W, .922 * H, .2 * H, fill=T["shell"], outline="", tags="shell")
        sx0, sy0, sx1, sy1 = .163 * W, .12 * H, .876 * W, .908 * H
        c.create_rectangle(sx0 - 5, sy0 - 5, sx1 + 5, sy1 + 5, fill=T["border"], outline="", tags="shell")
        self.pantalla.place(x=sx0, y=sy0, width=sx1 - sx0, height=sy1 - sy0)

        # Joystick (círculo beige, izquierda)
        cx, cy, r = .098 * W, .345 * H, 60 * u
        c.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#ede2b0", outline="#b8ad7d", width=3, tags=("shell", "joy"))
        c.create_oval(cx - r * .5, cy - r * .5, cx + r * .5, cy + r * .5, fill="#e0d398", outline="#b8ad7d",
                      width=2, tags=("shell", "joy"))

        # Cruceta (izquierda)
        cx, cy, a, w = .10 * W, .53 * H, 50 * u, 19 * u
        brazos = {"dp_up": ([cx - w, cy - w, cx - w, cy - a, cx + w, cy - a, cx + w, cy - w], cx, cy - a + 14 * u, "▲"),
                  "dp_down": ([cx - w, cy + w, cx - w, cy + a, cx + w, cy + a, cx + w, cy + w], cx, cy + a - 14 * u, "▼"),
                  "dp_left": ([cx - w, cy - w, cx - a, cy - w, cx - a, cy + w, cx - w, cy + w], cx - a + 14 * u, cy, "◀"),
                  "dp_right": ([cx + w, cy - w, cx + a, cy - w, cx + a, cy + w, cx + w, cy + w], cx + a - 14 * u, cy, "▶")}
        for tag, (pts, tx, ty, flecha) in brazos.items():
            c.create_polygon(pts, fill="#111111", outline="#000000", tags=("shell", tag))
            c.create_text(tx, ty, text=flecha, fill="#7a7a7a", font=("Arial", max(7, int(9 * u))), tags=("shell", tag))
        c.create_rectangle(cx - w, cy - w, cx + w, cy + w, fill="#111111", outline="#111111", tags="shell")

        # Botón gris (derecha)
        cx, cy, r = .935 * W, .34 * H, 46 * u
        c.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#7f7f7f", outline="#5a5a5a", width=3, tags=("shell", "gris"))

        # Botones B, Y, X, A
        for letra, fx, fy in (("B", .925, .45), ("Y", .908, .495), ("X", .93, .522), ("A", .957, .483)):
            bx, by, br = fx * W, fy * H, 16 * u
            tag = f"btn_{letra}"
            c.create_oval(bx - br, by - br, bx + br, by + br, fill="#1a8f3c", outline="#126b2c", width=2, tags=("shell", tag))
            c.create_text(bx, by, text=letra, fill="#b5e61d", font=("Arial", max(8, int(12 * u)), "bold"), tags=("shell", tag))

    def _controles(self) -> None:
        c = self.canvas
        acciones = {"joy": lambda: self.enfocar_busqueda(), "gris": self.pantalla_completa,
                    "dp_up": lambda: self.mover_sel(-1), "dp_down": lambda: self.mover_sel(1),
                    "dp_left": lambda: self.cambiar_tab(-1), "dp_right": lambda: self.cambiar_tab(1),
                    "btn_A": self.boton_a, "btn_B": lambda: self.mostrar_tab("inicio"),
                    "btn_X": self.juego_aleatorio, "btn_Y": self.boton_y}
        for tag, fn in acciones.items():
            c.tag_bind(tag, "<Button-1>", lambda e, f=fn: f())
            c.tag_bind(tag, "<Enter>", lambda e, t=tag: (c.config(cursor="hand2"), self.status(PISTAS[t])))
            c.tag_bind(tag, "<Leave>", lambda e: c.config(cursor=""))

    def cambiar_tab(self, d: int) -> None:
        claves = [t[0] for t in TABS]
        self.mostrar_tab(claves[(claves.index(self.tab_actual) + d) % len(claves)])

    def mover_sel(self, d: int) -> None:
        if self.tab_actual != "juegos":
            self.mostrar_tab("juegos")
        filas = self.tree.get_children()
        if not filas:
            return
        sel = self.tree.selection()
        i = filas.index(sel[0]) + d if sel else 0
        nueva = filas[max(0, min(len(filas) - 1, i))]
        self.tree.selection_set(nueva)
        self.tree.see(nueva)
        self.tree.focus(nueva)

    def boton_a(self) -> None:
        if self.tab_actual == "juegos" and self.tree.selection():
            self.jugar_seleccion()
        else:
            self.mostrar_tab("juegos")
            self.status("Elige un juego con ▲ ▼ y pulsa A")

    def boton_y(self) -> None:
        if self.tab_actual == "juegos" and self.tree.selection():
            self.toggle_fav()
        else:
            self.status("Selecciona un juego en la pestaña JUEGOS")

    # ------------------------------------------------------------- UI (dentro de la pantalla)
    def estilo(self) -> None:
        T = self.T
        self.root.configure(bg=T["desk"])
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Treeview", background=T["panel"], fieldbackground=T["panel"],
                    foreground=T["fg"], rowheight=26, borderwidth=0)
        s.map("Treeview", background=[("selected", T["accent"])], foreground=[("selected", "white")])
        s.configure("Treeview.Heading", background=T["button"], foreground="white",
                    font=("Arial", 10, "bold"), relief="flat")
        s.map("Treeview.Heading", background=[("active", aclarar(T["button"]))])
        s.configure("TCombobox", fieldbackground=T["panel"], background=T["button"], foreground=T["fg"])
        s.configure("Vertical.TScrollbar", background=T["button"], troughcolor=T["panel"], bordercolor=T["panel"])

    def btn(self, parent, texto, cmd, color=None, **kw) -> tk.Button:
        color = color or self.T["button"]
        b = tk.Button(parent, text=texto, command=cmd, bg=color, fg="white",
                      activebackground=aclarar(color), activeforeground="white",
                      relief="flat", cursor="hand2", padx=8, pady=5, **kw)
        b.bind("<Enter>", lambda e: b.config(bg=aclarar(color)))
        b.bind("<Leave>", lambda e: b.config(bg=color))
        return b

    def lbl(self, parent, texto="", size=11, bold=False, muted=False, **kw) -> tk.Label:
        T = self.T
        bg = kw.pop("bg", T["bg"])
        fg = kw.pop("fg", T["muted"] if muted else T["fg"])
        return tk.Label(parent, text=texto, bg=bg, fg=fg,
                        font=("Arial", size, "bold" if bold else "normal"), **kw)

    def construir_ui(self) -> None:
        for w in self.pantalla.winfo_children():
            w.destroy()
        self.estilo()
        T = self.T
        self.menu()
        self.pantalla.configure(bg=T["bg"])
        self.dibujar_consola()

        # Barra de estado (abajo)
        self.lbl_status = tk.Label(self.pantalla, text="Listo", anchor="w", bg=T["panel"],
                                   fg=T["muted"], padx=10, font=("Arial", 9))
        self.lbl_status.pack(side="bottom", fill="x")

        # Cabecera: DAVID (rojo) + EUSA (gris con borde y sombra), como en el dibujo
        cab = tk.Canvas(self.pantalla, height=62, bg=T["bg"], highlightthickness=0)
        cab.pack(fill="x", padx=14, pady=(8, 0))
        f1 = tkfont.Font(family="Arial", size=34, weight="bold")
        f2 = tkfont.Font(family="Arial Black", size=30, weight="bold")
        cab.create_text(4, 32, text="DAVID", anchor="w", font=f1, fill=T["accent"])
        x = 4 + f1.measure("DAVID ") + 6
        cab.create_text(x + 4, 36, text="EUSA", anchor="w", font=f2, fill="#ffffff")
        for dx, dy in ((-2, -2), (2, -2), (-2, 2), (2, 2), (0, -2), (0, 2), (-2, 0), (2, 0)):
            cab.create_text(x + dx, 32 + dy, text="EUSA", anchor="w", font=f2, fill="#000000")
        cab.create_text(x, 32, text="EUSA", anchor="w", font=f2, fill="#7f7f7f")
        self.lbl_reloj = tk.Label(cab, text="", bg=T["bg"], fg=T["muted"], font=("Arial", 9))
        self.lbl_reloj.place(relx=1.0, x=-2, y=44, anchor="e")

        # Barra de pestañas: icono encima y recuadro morado debajo
        barra = tk.Frame(self.pantalla, bg=T["bg"])
        barra.pack(fill="x", padx=14, pady=(2, 6))
        self.celdas = {}
        for col, (clave, texto, icono, peso) in enumerate(TABS):
            barra.grid_columnconfigure(col, weight=peso, uniform="tabs")
            ic = tk.Label(barra, text=icono, font=("Segoe UI Emoji", 17), bg=T["bg"], fg=T["fg"])
            ic.grid(row=0, column=col)
            celda = tk.Frame(barra, bg=T["bg"], highlightbackground=T["tabline"], highlightthickness=3)
            celda.grid(row=1, column=col, sticky="nsew")
            lb = tk.Label(celda, text=texto, font=("Arial Black", 10, "italic underline"), bg=T["bg"], fg=T["fg"])
            lb.pack(expand=True, pady=8, padx=2)
            for w in (ic, celda, lb):
                w.config(cursor="hand2")
                w.bind("<Button-1>", lambda e, k=clave: self.mostrar_tab(k))
            self.celdas[clave] = (celda, lb)

        # Páginas apiladas
        cont = tk.Frame(self.pantalla, bg=T["bg"])
        cont.pack(fill="both", expand=True, padx=14, pady=(0, 6))
        cont.grid_rowconfigure(0, weight=1)
        cont.grid_columnconfigure(0, weight=1)
        self.paginas = {}
        for clave, *_ in TABS:
            p = tk.Frame(cont, bg=T["bg"])
            p.grid(row=0, column=0, sticky="nsew")
            self.paginas[clave] = p
        self.tab_inicio, self.tab_web = self.paginas["inicio"], self.paginas["web"]
        self.tab_juegos, self.tab_util = self.paginas["juegos"], self.paginas["util"]
        self.tab_notas = self.paginas["notas"]

        self.construir_inicio()
        self.construir_web()
        self.construir_juegos()
        self.construir_util()
        self.construir_notas()
        self.mostrar_tab(self.tab_actual)
        self.actualizar_titulo()

    def mostrar_tab(self, clave: str) -> None:
        T = self.T
        self.tab_actual = clave
        self.paginas[clave].tkraise()
        for k, (celda, lb) in self.celdas.items():
            fondo = T["panel"] if k == clave else T["bg"]
            celda.config(bg=fondo)
            lb.config(bg=fondo)

    def menu(self) -> None:
        m = tk.Menu(self.root)
        archivo = tk.Menu(m, tearoff=0)
        archivo.add_command(label="Exportar biblioteca (JSON)", command=self.exportar_json)
        archivo.add_command(label="Importar biblioteca (JSON)", command=self.importar_json)
        archivo.add_command(label="Exportar juegos a CSV", command=self.exportar_csv)
        archivo.add_command(label="Crear backup ahora", command=self.backup_manual)
        archivo.add_separator()
        archivo.add_command(label="Salir  (Ctrl+Q)", command=self.salir)
        m.add_cascade(label="Archivo", menu=archivo)

        ver = tk.Menu(m, tearoff=0)
        for nombre in THEMES:
            ver.add_command(label=f"Tema {nombre}", command=lambda n=nombre: self.cambiar_tema(n))
        ver.add_command(label="Color de acento…", command=self.elegir_acento)
        ver.add_command(label="Quitar color personalizado", command=lambda: self.cambiar_acento(None))
        ver.add_separator()
        ver.add_command(label="Pantalla completa (F11)", command=self.pantalla_completa)
        ver.add_command(label="Actualizar (F5)", command=self.refrescar_todo)
        m.add_cascade(label="Ver", menu=ver)

        opc = tk.Menu(m, tearoff=0)
        self._v_confirm = tk.BooleanVar(value=self.cfg["confirm_exit"])
        self._v_window = tk.BooleanVar(value=self.cfg["new_window"])
        opc.add_checkbutton(label="Confirmar al salir", variable=self._v_confirm,
                            command=lambda: self._set_opt("confirm_exit", self._v_confirm.get()))
        opc.add_checkbutton(label="Abrir webs en ventana nueva", variable=self._v_window,
                            command=lambda: self._set_opt("new_window", self._v_window.get()))
        opc.add_separator()
        opc.add_command(label="Sincronizar juegos instalados de Epic Games", command=self.sincronizar_epic)
        opc.add_command(label="Escanear carpeta de juegos…", command=self.escanear_carpeta)
        opc.add_command(label="Restaurar catálogos (Steam + Epic)", command=self.restaurar_catalogo)
        opc.add_command(label="Verificar rutas de juegos", command=self.verificar_rutas)
        opc.add_command(label="Restablecer configuración", command=self.restablecer)
        m.add_cascade(label="Opciones", menu=opc)

        ayuda = tk.Menu(m, tearoff=0)
        ayuda.add_command(label="Atajos y botones de la consola", command=self.mostrar_atajos)
        ayuda.add_command(label="Acerca de", command=lambda: messagebox.showinfo(
            "Acerca de", "David EUSA v3.0\nConsola lanzadora de apps web y juegos.\n"
                         f"Config: {CONFIG_DIR}"))
        m.add_cascade(label="Ayuda", menu=ayuda)
        self.root.config(menu=m)

    def _set_opt(self, clave: str, valor) -> None:
        self.cfg[clave] = valor
        self.guardar()

    # ------------------------------------------------------------- Inicio
    def construir_inicio(self) -> None:
        T = self.T
        for w in self.tab_inicio.winfo_children():
            w.destroy()
        h = datetime.now().hour
        saludo = "Buenos días" if h < 12 else "Buenas tardes" if h < 20 else "Buenas noches"
        self.lbl(self.tab_inicio, f"{saludo}, David 👋", 17, True).pack(pady=(10, 6))

        g = self.cfg["games"]
        stats = [("Juegos", len(g)), ("Favoritos", sum(x["favorite"] for x in g)),
                 ("Partidas", sum(x["plays"] for x in g)),
                 ("Tiempo", fmt_tiempo(sum(x["seconds"] for x in g))),
                 ("Apps web", len(self.cfg["webapps"]))]
        fila = tk.Frame(self.tab_inicio, bg=T["bg"])
        fila.pack(pady=4)
        for nombre, valor in stats:
            c = tk.Frame(fila, bg=T["panel"], padx=11, pady=8)
            c.pack(side="left", padx=4)
            self.lbl(c, str(valor), 15, True, bg=T["panel"], fg=T["accent"]).pack()
            self.lbl(c, nombre, 9, muted=True, bg=T["panel"]).pack()

        cols = tk.Frame(self.tab_inicio, bg=T["bg"])
        cols.pack(fill="both", expand=True, pady=8)
        top = sorted(g, key=lambda x: x["plays"], reverse=True)[:5]
        rec = sorted([x for x in g if x["last_played"]], key=lambda x: x["last_played"], reverse=True)[:5]
        for titulo, datos, fmt in (("🏆 Más jugados", top, lambda x: f"{x['name']}  ·  {x['plays']}"),
                                   ("🕒 Recientes", rec, lambda x: f"{x['name']}  ·  {x['last_played']}")):
            caja = tk.LabelFrame(cols, text=f" {titulo} ", bg=T["bg"], fg=T["fg"], font=("Arial", 10, "bold"))
            caja.pack(side="left", fill="both", expand=True, padx=4)
            for x in (datos if any(d["plays"] for d in datos) or titulo.startswith("🕒") else []) or [None]:
                self.lbl(caja, fmt(x) if x else "Aún no hay datos", 9, muted=not x).pack(anchor="w", padx=8, pady=2)

        self.btn(self.tab_inicio, "🎲 ¡Sorpréndeme con un juego!", self.juego_aleatorio,
                 T["accent"]).pack(pady=8)

    # ------------------------------------------------------------- Apps web
    def construir_web(self) -> None:
        T = self.T
        for w in self.tab_web.winfo_children():
            w.destroy()
        barra = tk.Frame(self.tab_web, bg=T["bg"])
        barra.pack(fill="x", pady=8)
        self.btn(barra, "➕ Añadir app", self.anadir_web, T["accent"]).pack(side="left", padx=4)
        self.btn(barra, "🚀 Abrir todas", self.abrir_todas_web).pack(side="left", padx=4)
        self.lbl(barra, "Clic derecho en una app: editar / eliminar / copiar URL", 8, muted=True).pack(side="left", padx=8)

        grid = tk.Frame(self.tab_web, bg=T["bg"])
        grid.pack(fill="both", expand=True)
        for i, app in enumerate(self.cfg["webapps"]):
            b = self.btn(grid, app["name"], lambda a=app: self.abrir_url(a["url"]), width=18, height=2)
            b.grid(row=i // 3, column=i % 3, padx=6, pady=6)
            Tooltip(b, app["url"])
            b.bind("<Button-3>", lambda e, a=app: self.menu_web(e, a))
            b.bind("<Button-2>", lambda e, a=app: self.menu_web(e, a))

    def abrir_url(self, url: str) -> None:
        import webbrowser as wb
        (wb.open_new if self.cfg["new_window"] else wb.open_new_tab)(url)
        self.status(f"Abierto: {url}")

    def abrir_todas_web(self) -> None:
        n = len(self.cfg["webapps"])
        if n > 3 and not messagebox.askyesno("Abrir todas", f"¿Abrir las {n} apps a la vez?"):
            return
        for a in self.cfg["webapps"]:
            self.abrir_url(a["url"])

    def menu_web(self, ev, app: dict) -> None:
        m = tk.Menu(self.root, tearoff=0)
        m.add_command(label="Editar", command=lambda: self.editar_web(app))
        m.add_command(label="Copiar URL", command=lambda: self.copiar(app["url"]))
        m.add_command(label="Eliminar", command=lambda: self.eliminar_web(app))
        m.tk_popup(ev.x_root, ev.y_root)

    def copiar(self, texto: str) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(texto)
        self.status("Copiado al portapapeles")

    def anadir_web(self) -> None:
        self.editar_web(None)

    def editar_web(self, app: dict | None) -> None:
        r = self.formulario("Editar app web" if app else "Nueva app web",
                            [("name", "Nombre", "text"), ("url", "URL", "text")], app)
        if not r:
            return
        url = normalizar_url(r["url"])
        if not r["name"] or not url:
            messagebox.showwarning("Datos inválidos", "Pon un nombre y una URL válida (ej. midominio.com).")
            return
        if app:
            app.update(name=r["name"], url=url)
        else:
            self.cfg["webapps"].append({"name": r["name"], "url": url})
        self.guardar()
        self.refrescar_todo()

    def eliminar_web(self, app: dict) -> None:
        if messagebox.askyesno("Eliminar", f"¿Eliminar «{app['name']}»?"):
            self.cfg["webapps"].remove(app)
            self.guardar()
            self.refrescar_todo()

    # ------------------------------------------------------------- Juegos
    def construir_juegos(self) -> None:
        T = self.T
        for w in self.tab_juegos.winfo_children():
            w.destroy()
        barra = tk.Frame(self.tab_juegos, bg=T["bg"])
        barra.pack(fill="x", pady=6)
        self.lbl(barra, "🔎").pack(side="left")
        self.entry_busq = tk.Entry(barra, textvariable=self.var_busqueda, width=14,
                                   bg=T["panel"], fg=T["fg"], insertbackground=T["fg"], relief="flat")
        self.entry_busq.pack(side="left", padx=4, ipady=4)
        cb = ttk.Combobox(barra, textvariable=self.var_cat, values=["Todas"] + CATEGORIAS,
                          width=10, state="readonly")
        cb.pack(side="left", padx=4)
        cb.bind("<<ComboboxSelected>>", lambda e: self.refrescar_juegos())
        tk.Checkbutton(barra, text="★ Favs", variable=self.var_fav, command=self.refrescar_juegos,
                       bg=T["bg"], fg=T["fg"], selectcolor=T["panel"], activebackground=T["bg"],
                       activeforeground=T["fg"]).pack(side="left", padx=2)
        b_add = self.btn(barra, "➕", self.anadir_juego, T["accent"])
        b_add.pack(side="right", padx=2)
        Tooltip(b_add, "Añadir juego (Ctrl+N)")
        b_scan = self.btn(barra, "📂", self.escanear_carpeta)
        b_scan.pack(side="right", padx=2)
        Tooltip(b_scan, "Escanear una carpeta de juegos")
        self.btn(barra, "▶ Jugar", self.jugar_seleccion).pack(side="right", padx=2)

        cols = {"fav": ("★", 34), "name": ("Nombre", 190), "category": ("Categoría", 90),
                "plays": ("Partidas", 64), "last": ("Último", 116), "time": ("Tiempo", 84)}
        self.tree = ttk.Treeview(self.tab_juegos, columns=list(cols), show="headings", selectmode="browse")
        for k, (t, w) in cols.items():
            self.tree.heading(k, text=t, command=lambda c=k: self.ordenar(c))
            self.tree.column(k, width=w, anchor="center" if k != "name" else "w", stretch=(k == "name"))
        sb = ttk.Scrollbar(self.tab_juegos, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self.jugar_seleccion())
        self.tree.bind("<Button-3>", self.menu_juego)
        self.tree.bind("<Return>", lambda e: self.jugar_seleccion())
        self.tree.bind("<Delete>", lambda e: self.eliminar_juego())
        self.refrescar_juegos()

    def enfocar_busqueda(self) -> None:
        self.mostrar_tab("juegos")
        self.entry_busq.focus_set()

    def ordenar(self, col: str) -> None:
        self.sort_rev = not self.sort_rev if self.sort_col == col else False
        self.sort_col = col
        self.refrescar_juegos()

    def refrescar_juegos(self) -> None:
        if not hasattr(self, "tree") or not self.tree.winfo_exists():
            return
        claves = {"fav": lambda g: g["favorite"], "name": lambda g: g["name"].lower(),
                  "category": lambda g: g["category"], "plays": lambda g: g["plays"],
                  "last": lambda g: g["last_played"], "time": lambda g: g["seconds"]}
        q, cat = self.var_busqueda.get().lower(), self.var_cat.get()
        filas = [(i, g) for i, g in enumerate(self.cfg["games"])
                 if q in g["name"].lower() and (cat == "Todas" or g["category"] == cat)
                 and (not self.var_fav.get() or g["favorite"])]
        filas.sort(key=lambda t: claves[self.sort_col](t[1]), reverse=self.sort_rev)
        previa = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for i, g in filas:
            self.tree.insert("", "end", iid=str(i), values=(
                "★" if g["favorite"] else "", g["name"], g["category"], g["plays"],
                g["last_played"] or "—", fmt_tiempo(g["seconds"])))
        if previa and self.tree.exists(previa[0]):
            self.tree.selection_set(previa[0])
        self.status(f"{len(filas)} de {len(self.cfg['games'])} juegos")

    def juego_sel(self) -> dict | None:
        s = self.tree.selection()
        return self.cfg["games"][int(s[0])] if s else None

    def menu_juego(self, ev) -> None:
        fila = self.tree.identify_row(ev.y)
        if not fila:
            return
        self.tree.selection_set(fila)
        g = self.juego_sel()
        m = tk.Menu(self.root, tearoff=0)
        m.add_command(label="▶ Jugar", command=self.jugar_seleccion)
        m.add_command(label="☆ Quitar favorito" if g["favorite"] else "★ Marcar favorito", command=self.toggle_fav)
        m.add_command(label="Editar", command=self.editar_juego)
        m.add_command(label="Abrir carpeta del juego", command=self.abrir_carpeta_juego)
        m.add_command(label="Eliminar", command=self.eliminar_juego)
        m.tk_popup(ev.x_root, ev.y_root)

    def formulario(self, titulo: str, campos: list, inicial: dict | None = None) -> dict | None:
        T = self.T
        win = tk.Toplevel(self.root)
        win.title(titulo)
        win.configure(bg=T["bg"])
        win.transient(self.root)
        win.grab_set()
        vars_, res = {}, {}
        for i, (clave, etiqueta, tipo, *extra) in enumerate(campos):
            self.lbl(win, etiqueta).grid(row=i, column=0, sticky="e", padx=10, pady=6)
            v = tk.StringVar(value=str((inicial or {}).get(clave, extra[1] if len(extra) > 1 else "")))
            vars_[clave] = v
            if tipo == "combo":
                w = ttk.Combobox(win, textvariable=v, values=extra[0], width=38)
            else:
                w = tk.Entry(win, textvariable=v, width=42)
            w.grid(row=i, column=1, padx=6, pady=6)
            if i == 0:
                w.focus_set()
            if tipo == "file":
                self.btn(win, "…", lambda v=v: v.set(filedialog.askopenfilename() or v.get())).grid(row=i, column=2, padx=6)

        def ok() -> None:
            res.update({k: v.get().strip() for k, v in vars_.items()})
            win.destroy()

        f = tk.Frame(win, bg=T["bg"])
        f.grid(row=len(campos), column=0, columnspan=3, pady=10)
        self.btn(f, "Guardar", ok, T["accent"]).pack(side="left", padx=6)
        self.btn(f, "Cancelar", win.destroy).pack(side="left", padx=6)
        win.bind("<Return>", lambda e: ok())
        win.bind("<Escape>", lambda e: win.destroy())
        self.root.wait_window(win)
        return res or None

    CAMPOS_JUEGO = [("name", "Nombre", "text"), ("path", "Ruta / URI", "file"),
                    ("category", "Categoría", "combo", CATEGORIAS)]

    def anadir_juego(self) -> None:
        r = self.formulario("Añadir juego", self.CAMPOS_JUEGO, {"category": "Otros"})
        if r and r["name"] and r["path"]:
            self.cfg["games"].append(_juego(r["name"], r["path"], r["category"] or "Otros"))
            self.guardar()
            self.refrescar_todo()
        elif r:
            messagebox.showwarning("Faltan datos", "El nombre y la ruta son obligatorios.")

    def editar_juego(self) -> None:
        g = self.juego_sel()
        if not g:
            return
        r = self.formulario("Editar juego", self.CAMPOS_JUEGO, g)
        if r and r["name"] and r["path"]:
            g.update(name=r["name"], path=r["path"], category=r["category"] or "Otros")
            self.guardar()
            self.refrescar_todo()

    def eliminar_juego(self) -> None:
        g = self.juego_sel()
        if g and messagebox.askyesno("Eliminar", f"¿Eliminar «{g['name']}» de la biblioteca?"):
            self.cfg["games"].remove(g)
            self.guardar()
            self.refrescar_todo()

    def toggle_fav(self) -> None:
        g = self.juego_sel()
        if g:
            g["favorite"] = not g["favorite"]
            self.guardar()
            self.refrescar_todo()

    def abrir_carpeta_juego(self) -> None:
        g = self.juego_sel()
        if not g or es_protocolo(g["path"]):
            self.status("Este juego se lanza por protocolo; no tiene carpeta.")
            return
        abrir_con_sistema(str(Path(g["path"]).parent))

    def jugar_seleccion(self) -> None:
        g = self.juego_sel()
        if g:
            self.lanzar_juego(g)
        else:
            self.status("Selecciona un juego primero")

    def juego_aleatorio(self) -> None:
        if not self.cfg["games"]:
            return messagebox.showinfo("Sin juegos", "Añade juegos primero.")
        g = random.choice(self.cfg["games"])
        if messagebox.askyesno("Sorpresa", f"¿Jugamos a «{g['name']}»?"):
            self.lanzar_juego(g)

    def lanzar_juego(self, g: dict) -> None:
        ruta = g["path"]
        try:
            proc = None
            tienda = ruta.startswith(("http://", "https://"))
            if es_protocolo(ruta):
                abrir_con_sistema(ruta) if sys.platform.startswith("win") else webbrowser.open(ruta)
            elif not Path(ruta).exists():
                return messagebox.showerror("Error", f"No se encontró el juego en:\n{ruta}")
            elif ruta.lower().endswith(".exe") or os.access(ruta, os.X_OK):
                proc = subprocess.Popen([ruta], cwd=str(Path(ruta).parent))
            else:
                abrir_con_sistema(ruta)
            if tienda:  # enlace a la tienda de Epic: no cuenta como partida
                self.status(f"Abriendo la tienda de Epic para «{g['name']}». Sincroniza Epic para lanzarlo directo.")
                return
            g["plays"] += 1
            g["last_played"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.guardar()
            self.refrescar_todo()
            self.status(f"Iniciado: {g['name']}")
            if proc:  # hilo aparte: mide el tiempo sin bloquear la interfaz
                threading.Thread(target=self._vigilar, args=(proc, g, time.time()), daemon=True).start()
        except Exception as e:
            logging.exception("Fallo al lanzar %s", ruta)
            messagebox.showerror("Error", f"No se pudo iniciar el juego:\n{e}")

    def _vigilar(self, proc: subprocess.Popen, g: dict, t0: float) -> None:
        proc.wait()
        self.cola.put((g, int(time.time() - t0)))

    def sincronizar_epic(self) -> None:
        instalados = leer_epic_instalados()
        if not instalados:
            return messagebox.showinfo(
                "Epic Games", "No encontré juegos instalados del Epic Games Launcher.\n"
                              "(Solo funciona en Windows con el launcher instalado.)")
        por_nombre = {_norm(g["name"]): g for g in self.cfg["games"]}
        actualizados = nuevos = 0
        for nombre, uri in instalados:
            g = por_nombre.get(_norm(nombre))
            if g:
                g["path"] = uri
                actualizados += 1
            else:
                self.cfg["games"].append(_juego(nombre, uri, "Otros"))
                nuevos += 1
        self.guardar()
        self.refrescar_todo()
        messagebox.showinfo("Epic Games", f"Juegos de Epic vinculados: {actualizados}\nNuevos añadidos: {nuevos}")

    def escanear_carpeta(self) -> None:
        carpeta = filedialog.askdirectory(title="Carpeta con juegos")
        if not carpeta:
            return
        existentes = {g["path"] for g in self.cfg["games"]}
        base, nuevos = Path(carpeta), []
        for exe in base.rglob("*.exe"):
            if len(exe.relative_to(base).parts) > 3 or any(x in exe.name.lower() for x in IGNORAR_EXE):
                continue
            if str(exe) not in existentes:
                nuevos.append(exe)
            if len(nuevos) >= 200:
                break
        if not nuevos:
            return messagebox.showinfo("Escaneo", "No se encontraron juegos nuevos.")
        if messagebox.askyesno("Escaneo", f"Se encontraron {len(nuevos)} ejecutables nuevos. ¿Añadirlos?"):
            for exe in nuevos:
                self.cfg["games"].append(_juego(exe.stem, str(exe), "Otros"))
            self.guardar()
            self.refrescar_todo()

    def restaurar_catalogo(self) -> None:
        n = anadir_catalogo(self.cfg)
        self.guardar()
        self.refrescar_todo()
        messagebox.showinfo("Catálogo", f"Se añadieron {n} juegos." if n else "Los catálogos ya estaban completos ✔")

    def verificar_rutas(self) -> None:
        rotas = [g["name"] for g in self.cfg["games"]
                 if not es_protocolo(g["path"]) and not Path(g["path"]).exists()]
        messagebox.showinfo("Verificación", "Todas las rutas son válidas ✔" if not rotas
                            else "Rutas no encontradas:\n\n• " + "\n• ".join(rotas))

    # ------------------------------------------------------------- Utilidades
    def construir_util(self) -> None:
        T = self.T
        for w in self.tab_util.winfo_children():
            w.destroy()
        so = sys.platform
        calc = "calc" if so.startswith("win") else "gnome-calculator" if so.startswith("linux") else "open -a Calculator"
        nota = "notepad" if so.startswith("win") else "gedit" if so.startswith("linux") else "open -a TextEdit"
        items = [("🧮 Calculadora", lambda: self.ejecutar(calc)),
                 ("🗒 Bloc de notas", lambda: self.ejecutar(nota)),
                 ("📁 Carpeta de usuario", lambda: abrir_con_sistema(str(Path.home()))),
                 ("⚙ Carpeta de config", lambda: abrir_con_sistema(str(CONFIG_DIR))),
                 ("📜 Ver log", lambda: abrir_con_sistema(str(LOG_FILE)) if LOG_FILE.exists() else None),
                 ("💻 Info del sistema", self.info_sistema)]
        grid = tk.Frame(self.tab_util, bg=T["bg"])
        grid.pack(pady=24)
        for i, (t, c) in enumerate(items):
            self.btn(grid, t, c, width=18, height=2).grid(row=i // 3, column=i % 3, padx=6, pady=8)

    def ejecutar(self, cmd: str) -> None:
        try:
            subprocess.Popen(cmd.split())
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo ejecutar «{cmd}»:\n{e}")

    def info_sistema(self) -> None:
        messagebox.showinfo("Sistema", f"SO: {platform.system()} {platform.release()}\n"
                                       f"Máquina: {platform.machine()}\nCPU núcleos: {os.cpu_count()}\n"
                                       f"Python: {platform.python_version()}\nUsuario: {os.getlogin() if hasattr(os, 'getlogin') else '-'}")

    # ------------------------------------------------------------- Notas
    def construir_notas(self) -> None:
        T = self.T
        self.txt = tk.Text(self.tab_notas, bg=T["panel"], fg=T["fg"], insertbackground=T["fg"],
                           relief="flat", font=("Consolas", 11), wrap="word", padx=10, pady=10, undo=True)
        self.txt.pack(fill="both", expand=True)
        self.txt.insert("1.0", self.cfg["notes"])
        self.txt.bind("<KeyRelease>", self._nota_cambio)

    def _nota_cambio(self, _=None) -> None:
        if self.notes_job:
            self.root.after_cancel(self.notes_job)
        self.notes_job = self.root.after(800, self._guardar_nota)

    def _guardar_nota(self) -> None:
        self.cfg["notes"] = self.txt.get("1.0", "end-1c")
        self.guardar()
        self.status("Notas guardadas ✔")

    # ------------------------------------------------------------- Temas
    def cambiar_tema(self, nombre: str) -> None:
        self.cfg["theme"] = nombre
        self.cfg["accent"] = None
        self.guardar()
        self.construir_ui()

    def elegir_acento(self) -> None:
        c = colorchooser.askcolor(color=self.T["accent"], title="Color de acento")[1]
        if c:
            self.cambiar_acento(c)

    def cambiar_acento(self, c: str | None) -> None:
        self.cfg["accent"] = c
        self.guardar()
        self.construir_ui()

    # ------------------------------------------------------------- Datos
    def exportar_json(self) -> None:
        f = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if f:
            Path(f).write_text(json.dumps({"games": self.cfg["games"], "webapps": self.cfg["webapps"]},
                                          indent=2, ensure_ascii=False), "utf-8")
            self.status(f"Exportado a {f}")

    def importar_json(self) -> None:
        f = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not f:
            return
        try:
            datos = json.loads(Path(f).read_text("utf-8"))
            nombres = {g["name"] for g in self.cfg["games"]}
            urls = {a["url"] for a in self.cfg["webapps"]}
            self.cfg["games"] += [g for g in datos.get("games", []) if g["name"] not in nombres]
            self.cfg["webapps"] += [a for a in datos.get("webapps", []) if a["url"] not in urls]
            self.guardar()
            self.refrescar_todo()
            self.status("Importación completada")
        except Exception as e:
            messagebox.showerror("Error", f"Archivo no válido:\n{e}")

    def exportar_csv(self) -> None:
        f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if f:
            with open(f, "w", newline="", encoding="utf-8-sig") as fh:
                w = csv.DictWriter(fh, fieldnames=["name", "path", "category", "favorite", "plays", "last_played", "seconds"])
                w.writeheader()
                w.writerows(self.cfg["games"])
            self.status(f"CSV guardado en {f}")

    def backup_manual(self) -> None:
        self.guardar()
        hacer_backup()
        self.status(f"Backup creado en {BACKUP_DIR}")

    def restablecer(self) -> None:
        if messagebox.askyesno("Restablecer", "Se borrarán juegos, apps y notas. ¿Continuar?"):
            hacer_backup()
            self.cfg = copy.deepcopy(DEFAULT_CONFIG)
            self.guardar()
            self.construir_ui()

    def mostrar_atajos(self) -> None:
        messagebox.showinfo(
            "Botones y atajos",
            "BOTONES DE LA CONSOLA\n"
            "▲ ▼  Moverse por la lista de juegos\n◀ ▶  Cambiar de pestaña\n"
            "A  Jugar el juego seleccionado\nB  Ir a Inicio\nX  Juego aleatorio\nY  Favorito\n"
            "Joystick  Buscar juego      Botón gris  Pantalla completa\n\n"
            "TECLADO\nCtrl+1…5  Pestañas (Juegos, Utilidad, Apps Web, Inicio, Notas)\n"
            "Ctrl+←/→  Pestaña anterior/siguiente\nCtrl+F  Buscar      Ctrl+N  Añadir juego\n"
            "F5  Actualizar      F11  Pantalla completa      Ctrl+Q  Salir")

    # ------------------------------------------------------------- Ciclo
    def refrescar_todo(self) -> None:
        self.construir_inicio()
        self.construir_web()
        self.refrescar_juegos()
        self.actualizar_titulo()

    def actualizar_titulo(self) -> None:
        self.root.title(f"David EUSA — {len(self.cfg['games'])} juegos · {len(self.cfg['webapps'])} apps")

    def tick(self) -> None:
        """Cada segundo: actualiza el reloj y procesa tiempos de juego."""
        try:
            self.lbl_reloj.config(text=datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))
            while not self.cola.empty():
                g, seg = self.cola.get_nowait()
                g["seconds"] += seg
                self.guardar()
                self.refrescar_todo()
        except tk.TclError:
            pass
        self.root.after(1000, self.tick)

    def salir(self) -> None:
        if self.cfg["confirm_exit"] and not messagebox.askokcancel("Salir", "¿Cerrar David EUSA?"):
            return
        if not self.root.attributes("-fullscreen"):
            self.cfg["geometry"] = self.root.geometry()
        self.guardar()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    App().run()


# ============================================================================
# APÉNDICE v3.1 — Boot Screen + Personalización + Idiomas (ES / EN / PT)
# ----------------------------------------------------------------------------
# Todo lo anterior se mantiene intacto. Aquí solo se AÑADEN cosas:
#   · Diccionario de traducciones IDIOMAS (es / en / pt).
#   · PantallaArranque (Boot Screen) animada tipo consola retro.
#   · VentanaPersonalizar (botón 🎨).
#   · AppEUSA: subclase de App que añade el botón 🎨 y aplica idioma.
#   · Se redefine main() para arrancar AppEUSA en lugar de App.
# ============================================================================

IDIOMAS = {
    "es": {
        "nombre_idioma": "Español",
        "tabs": {"juegos": "JUEGOS", "util": "UTILIDAD", "web": "APPS WEB",
                 "inicio": "INICIO", "notas": "NOTAS"},
        "personalizar": "Personalizar consola",
        "personalizar_corto": "Personalizar",
        "personalizar_tooltip": "Personalizar la consola (tema, idioma, arranque)",
        "titulo_personalizar": "Personalizar consola",
        "seccion_apariencia": "🎨 Apariencia",
        "seccion_idioma": "🌐 Idioma",
        "seccion_arranque": "🚀 Pantalla de arranque",
        "tema": "Tema",
        "color_acento": "Color de acento",
        "elegir_color": "Elegir…",
        "quitar_color": "Quitar",
        "idioma": "Idioma",
        "boot_activar": "Mostrar pantalla de arranque al iniciar",
        "boot_duracion": "Duración (s)",
        "guardar": "Guardar",
        "cancelar": "Cancelar",
        "restaurar": "Restaurar",
        "guardado": "Personalización guardada ✔",
        "boot_titulo": "DAVID EUSA",
        "boot_subtitulo": "Consola lanzadora de apps web y juegos",
        "boot_mensajes": ["Cargando módulos…", "Preparando biblioteca de juegos…",
                          "Conectando con la consola…", "¡Listo!"],
        "boot_pulsa": "Pulsa cualquier tecla para continuar",
    },
    "en": {
        "nombre_idioma": "English",
        "tabs": {"juegos": "GAMES", "util": "TOOLS", "web": "WEB APPS",
                 "inicio": "HOME", "notas": "NOTES"},
        "personalizar": "Customize console",
        "personalizar_corto": "Customize",
        "personalizar_tooltip": "Customize the console (theme, language, boot)",
        "titulo_personalizar": "Customize console",
        "seccion_apariencia": "🎨 Appearance",
        "seccion_idioma": "🌐 Language",
        "seccion_arranque": "🚀 Boot screen",
        "tema": "Theme",
        "color_acento": "Accent color",
        "elegir_color": "Pick…",
        "quitar_color": "Clear",
        "idioma": "Language",
        "boot_activar": "Show boot screen on startup",
        "boot_duracion": "Duration (s)",
        "guardar": "Save",
        "cancelar": "Cancel",
        "restaurar": "Reset",
        "guardado": "Customization saved ✔",
        "boot_titulo": "DAVID EUSA",
        "boot_subtitulo": "Web apps & games launcher console",
        "boot_mensajes": ["Loading modules…", "Preparing game library…",
                          "Connecting to console…", "Ready!"],
        "boot_pulsa": "Press any key to continue",
    },
    "pt": {
        "nombre_idioma": "Português",
        "tabs": {"juegos": "JOGOS", "util": "UTILIDADES", "web": "APPS WEB",
                 "inicio": "INÍCIO", "notas": "NOTAS"},
        "personalizar": "Personalizar consola",
        "personalizar_corto": "Personalizar",
        "personalizar_tooltip": "Personalizar a consola (tema, idioma, arranque)",
        "titulo_personalizar": "Personalizar consola",
        "seccion_apariencia": "🎨 Aparência",
        "seccion_idioma": "🌐 Idioma",
        "seccion_arranque": "🚀 Tela de arranque",
        "tema": "Tema",
        "color_acento": "Cor de destaque",
        "elegir_color": "Escolher…",
        "quitar_color": "Limpar",
        "idioma": "Idioma",
        "boot_activar": "Mostrar tela de arranque ao iniciar",
        "boot_duracion": "Duração (s)",
        "guardar": "Guardar",
        "cancelar": "Cancelar",
        "restaurar": "Repor",
        "guardado": "Personalização guardada ✔",
        "boot_titulo": "DAVID EUSA",
        "boot_subtitulo": "Consola lançadora de apps web e jogos",
        "boot_mensajes": ["A carregar módulos…", "A preparar biblioteca de jogos…",
                          "A ligar à consola…", "Pronto!"],
        "boot_pulsa": "Pressione qualquer tecla para continuar",
    },
}


def tr(clave: str, idioma: str = "es"):
    """Traduce una clave al idioma indicado, con respaldo al español."""
    tabla = IDIOMAS.get(idioma, IDIOMAS["es"])
    if clave in tabla:
        return tabla[clave]
    return IDIOMAS["es"].get(clave, clave)


class PantallaArranque:
    """Ventana de arranque estilo consola retro (sin bordes, centrada)."""

    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
        self.idioma = cfg.get("language", "es")
        self.duracion = float(cfg.get("boot_duracion", 2.8))
        self.tema = THEMES.get(cfg.get("theme", "Consola"), THEMES["Consola"])
        self.acento = cfg.get("accent") or self.tema["accent"]

        self.W, self.H = 620, 360
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        x, y = (sw - self.W) // 2, (sh - self.H) // 2
        self.root.geometry(f"{self.W}x{self.H}+{x}+{y}")
        self.root.configure(bg="#0a0a0a")

        self.c = tk.Canvas(self.root, width=self.W, height=self.H,
                           bg="#0a0a0a", highlightthickness=0)
        self.c.pack(fill="both", expand=True)

        # Marco luminoso (usa los colores del tema Consola)
        self.c.create_rectangle(3, 3, self.W - 3, self.H - 3,
                                outline=self.tema["shell"], width=2)
        self.c.create_rectangle(8, 8, self.W - 8, self.H - 8,
                                outline=self.acento, width=1)

        # Título + subtítulo
        self.c.create_text(self.W / 2, 84, text=tr("boot_titulo", self.idioma),
                           fill=self.tema["shell"],
                           font=("Arial Black", 40, "bold"))
        self.c.create_text(self.W / 2, 128, text=tr("boot_subtitulo", self.idioma),
                           fill=self.tema["bg"],
                           font=("Arial", 10, "italic"))

        # Barra de progreso
        self.bar_x0, self.bar_x1 = 70, self.W - 70
        self.bar_y0, self.bar_y1 = 210, 234
        self.c.create_rectangle(self.bar_x0, self.bar_y0, self.bar_x1, self.bar_y1,
                                fill="#1a1a1a", outline="#2a2a2a")
        self.bar = self.c.create_rectangle(self.bar_x0, self.bar_y0,
                                           self.bar_x0, self.bar_y1,
                                           fill=self.acento, outline="")

        # Texto y porcentaje
        self.lbl_msg = self.c.create_text(self.W / 2, 268, text="", fill="#cfcfcf",
                                          font=("Consolas", 10))
        self.lbl_pct = self.c.create_text(self.W / 2, 298, text="0%",
                                          fill=self.tema["shell"],
                                          font=("Consolas", 14, "bold"))
        self.c.create_text(self.W / 2, 334, text=tr("boot_pulsa", self.idioma),
                           fill="#555555", font=("Arial", 8))

        self.mensajes = tr("boot_mensajes", self.idioma)
        # 25 ms por tick -> velocidad ajustada a la duración
        self.step = max(1, int(100 * 25 / max(300, self.duracion * 1000)))
        self.pct = 0
        self.cerrado = False

        self.root.bind("<Key>", lambda e: self.cerrar())
        self.root.bind("<Button-1>", lambda e: self.cerrar())
        self.root.after(30, self._tick)

    def _tick(self) -> None:
        if self.cerrado:
            return
        self.pct = min(100, self.pct + self.step)
        x1 = self.bar_x0 + (self.bar_x1 - self.bar_x0) * self.pct / 100
        self.c.coords(self.bar, self.bar_x0, self.bar_y0, x1, self.bar_y1)
        idx = min(len(self.mensajes) - 1, self.pct * len(self.mensajes) // 100)
        self.c.itemconfig(self.lbl_msg, text=self.mensajes[idx])
        self.c.itemconfig(self.lbl_pct, text=f"{self.pct}%")
        if self.pct >= 100:
            self.root.after(280, self.cerrar)
        else:
            self.root.after(25, self._tick)

    def cerrar(self) -> None:
        if self.cerrado:
            return
        self.cerrado = True
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def mostrar(self) -> None:
        self.root.mainloop()


def mostrar_boot(cfg: dict) -> None:
    """Muestra la pantalla de arranque si está activada. Silenciosa ante errores."""
    if not cfg.get("boot_enabled", True):
        return
    try:
        PantallaArranque(cfg).mostrar()
    except Exception:
        logging.exception("Fallo en la pantalla de arranque")


class VentanaPersonalizar(tk.Toplevel):
    """Ventana de personalización de la consola (tema, idioma, boot)."""

    def __init__(self, app: "AppEUSA") -> None:
        super().__init__(app.root)
        self.app = app
        T = app.T
        self.title(app.t("titulo_personalizar"))
        self.configure(bg=T["bg"])
        self.transient(app.root)
        self.grab_set()
        self.resizable(False, False)

        ancho, alto = 540, 560
        self._centrar(ancho, alto)

        tk.Label(self, text="🎨 " + app.t("titulo_personalizar"),
                 bg=T["bg"], fg=T["accent"],
                 font=("Arial Black", 16, "bold")).pack(pady=(16, 2))
        tk.Label(self, text="David EUSA · v3.1", bg=T["bg"], fg=T["muted"],
                 font=("Arial", 9, "italic")).pack()

        cont = tk.Frame(self, bg=T["bg"], padx=24, pady=8)
        cont.pack(fill="both", expand=True)

        # ---- Apariencia ------------------------------------------------
        self._seccion(cont, app.t("seccion_apariencia"))

        self.v_tema = tk.StringVar(value=app.cfg.get("theme", "Consola"))
        self._fila_combo(cont, app.t("tema"), self.v_tema, list(THEMES.keys()))

        self.v_acento = app.cfg.get("accent") or T["accent"]
        row = self._fila(cont, app.t("color_acento"))
        self.swatch = tk.Label(row, text="   ", bg=self.v_acento, width=4,
                               relief="solid", bd=1)
        self.swatch.pack(side="left", padx=4)
        self._btn(row, app.t("elegir_color"), self._pick_color).pack(side="left", padx=3)
        self._btn(row, app.t("quitar_color"), self._clear_color).pack(side="left", padx=3)

        # ---- Idioma ----------------------------------------------------
        self._seccion(cont, app.t("seccion_idioma"))
        row = self._fila(cont, app.t("idioma"))
        self.v_idioma = tk.StringVar(value=app.cfg.get("language", "es"))
        for code in ("es", "en", "pt"):
            tk.Radiobutton(row, text=IDIOMAS[code]["nombre_idioma"],
                           variable=self.v_idioma, value=code,
                           bg=T["bg"], fg=T["fg"], selectcolor=T["panel"],
                           activebackground=T["bg"], activeforeground=T["fg"],
                           font=("Arial", 10)).pack(side="left", padx=6)

        # ---- Arranque --------------------------------------------------
        self._seccion(cont, app.t("seccion_arranque"))
        self.v_boot = tk.BooleanVar(value=app.cfg.get("boot_enabled", True))
        tk.Checkbutton(cont, text=app.t("boot_activar"), variable=self.v_boot,
                       bg=T["bg"], fg=T["fg"], selectcolor=T["panel"],
                       activebackground=T["bg"], activeforeground=T["fg"],
                       font=("Arial", 10), anchor="w").pack(fill="x", pady=6, padx=2)

        row = self._fila(cont, app.t("boot_duracion"))
        self.v_dur = tk.DoubleVar(value=app.cfg.get("boot_duracion", 2.8))
        tk.Spinbox(row, from_=0.5, to=10.0, increment=0.5,
                   textvariable=self.v_dur, width=6,
                   bg=T["panel"], fg=T["fg"], relief="flat").pack(side="left", padx=4)

        # ---- Pie con botones ------------------------------------------
        pie = tk.Frame(self, bg=T["bg"], pady=12)
        pie.pack(fill="x", side="bottom")
        self._btn(pie, "💾 " + app.t("guardar"), self._guardar,
                  T["accent"]).pack(side="right", padx=8)
        self._btn(pie, app.t("cancelar"),
                  self.destroy).pack(side="right", padx=4)
        self._btn(pie, "↺ " + app.t("restaurar"),
                  self._restaurar).pack(side="left", padx=8)

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>", lambda e: self._guardar())

    # ------------------------------------------------------------- helpers
    def _centrar(self, w: int, h: int) -> None:
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{max(0, (sw - w) // 2)}+{max(0, (sh - h) // 2)}")

    def _seccion(self, parent, texto: str) -> None:
        T = self.app.T
        f = tk.Frame(parent, bg=T["bg"])
        f.pack(fill="x", pady=(12, 2))
        tk.Label(f, text=texto, bg=T["bg"], fg=T["accent"],
                 font=("Arial", 11, "bold")).pack(anchor="w")
        tk.Frame(f, bg=T["border"], height=1).pack(fill="x", pady=(2, 0))

    def _fila(self, parent, etiqueta: str) -> tk.Frame:
        T = self.app.T
        row = tk.Frame(parent, bg=T["bg"])
        row.pack(fill="x", pady=4)
        tk.Label(row, text=etiqueta + ":", bg=T["bg"], fg=T["fg"],
                 font=("Arial", 10), width=16, anchor="w").pack(side="left")
        return row

    def _fila_combo(self, parent, etiqueta, var, valores) -> None:
        row = self._fila(parent, etiqueta)
        cb = ttk.Combobox(row, textvariable=var, values=valores,
                          state="readonly", width=20)
        cb.pack(side="left")

    def _btn(self, parent, texto, cmd, color=None) -> tk.Button:
        T = self.app.T
        color = color or T["button"]
        b = tk.Button(parent, text=texto, command=cmd, bg=color, fg="white",
                      activebackground=aclarar(color), activeforeground="white",
                      relief="flat", cursor="hand2", padx=10, pady=4,
                      font=("Arial", 10, "bold"))
        b.bind("<Enter>", lambda e: b.config(bg=aclarar(color)))
        b.bind("<Leave>", lambda e: b.config(bg=color))
        return b

    # ------------------------------------------------------------- acciones
    def _pick_color(self) -> None:
        c = colorchooser.askcolor(color=self.v_acento,
                                  title=self.app.t("color_acento"))[1]
        if c:
            self.v_acento = c
            self.swatch.config(bg=c)

    def _clear_color(self) -> None:
        self.v_acento = None
        self.swatch.config(bg=self.app.T["button"])

    def _restaurar(self) -> None:
        self.v_tema.set("Consola")
        self.v_acento = None
        self.swatch.config(bg=self.app.T["button"])
        self.v_idioma.set("es")
        self.v_boot.set(True)
        self.v_dur.set(2.8)

    def _guardar(self) -> None:
        app = self.app
        app.cfg["theme"] = self.v_tema.get()
        app.cfg["accent"] = self.v_acento
        app.cfg["language"] = self.v_idioma.get()
        app.cfg["boot_enabled"] = bool(self.v_boot.get())
        app.cfg["boot_duracion"] = float(self.v_dur.get())
        app.idioma = app.cfg["language"]
        app.guardar()
        app.construir_ui()
        self.destroy()
        try:
            app.status(app.t("guardado"))
        except Exception:
            pass


class AppEUSA(App):
    """App original extendida con: Boot Screen, botón 🎨 y 3 idiomas (ES/EN/PT)."""

    def __init__(self) -> None:
        # 1) Cargar config UNA vez y fijar el idioma ANTES de crear el App,
        #    porque App.__init__ ya llama a construir_ui() -> _aplicar_idioma().
        cfg = cargar_config()
        self.idioma = cfg.get("language", "es")

        # 2) Boot Screen (antes de que exista la ventana principal)
        mostrar_boot(cfg)

        # 3) Arrancar el App original (no se modifica nada de su lógica)
        super().__init__()

        # 4) Re-sincronizar por si la config se migró/cambió al cargar
        self.idioma = self.cfg.get("language", self.idioma)

    # ------------------------------------------------------------- i18n
    def t(self, clave: str, por_defecto: str | None = None):
        idioma = getattr(self, "idioma",
                         self.cfg.get("language", "es") if hasattr(self, "cfg") else "es")
        val = tr(clave, idioma)
        if val == clave and por_defecto is not None:
            return por_defecto
        return val

    # ------------------------------------------------------------- UI extendida
    def construir_ui(self) -> None:
        super().construir_ui()
        self._aplicar_idioma()
        self._boton_personalizar()

    def _aplicar_idioma(self) -> None:
        """Traduce los textos de las pestañas visibles."""
        idioma = getattr(self, "idioma",
                         self.cfg.get("language", "es") if hasattr(self, "cfg") else "es")
        tabla = IDIOMAS.get(idioma, IDIOMAS["es"]).get("tabs", {})
        # Algunas llamadas a construir_ui() pueden ocurrir antes de crear self.celdas
        for clave, (celda, lb) in getattr(self, "celdas", {}).items():
            if clave in tabla:
                lb.config(text=tabla[clave])

    def _boton_personalizar(self) -> None:
        """Botón 🎨 en la esquina superior derecha de la pantalla."""
        T = self.T
        # Eliminar el anterior si existe (para no duplicar al reconstruir la UI)
        try:
            self.btn_personalizar.destroy()
        except Exception:
            pass

        b = tk.Button(
            self.pantalla,
            text="🎨 " + self.t("personalizar_corto"),
            command=self.abrir_personalizar,
            bg=T["button"], fg="white",
            activebackground=aclarar(T["button"]), activeforeground="white",
            relief="flat", cursor="hand2", padx=10, pady=3,
            font=("Arial", 9, "bold"), bd=0,
        )
        b.bind("<Enter>", lambda e: b.config(bg=aclarar(T["button"])))
        b.bind("<Leave>", lambda e: b.config(bg=T["button"]))
        b.place(relx=1.0, x=-14, y=8, anchor="ne")
        Tooltip(b, self.t("personalizar_tooltip"))
        self.btn_personalizar = b

    def abrir_personalizar(self) -> None:
        VentanaPersonalizar(self)

def main() -> None:  # type: ignore[no-redef]
    """Punto de entrada v3.1: arranca AppEUSA (boot + personalización + idiomas)."""
    AppEUSA().run()


if __name__ == "__main__":
    main()
