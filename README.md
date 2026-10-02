#  David EUSA

> Consola lanzadora de apps web y juegos con estética retro de consola portátil.  
> Hecha en Python + Tkinter, multiplataforma (Windows · Linux · macOS) y totalmente personalizable.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-22B14C)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-00A2E8)
![License](https://img.shields.io/badge/License-MIT-A349A4)
![Idiomas](https://img.shields.io/badge/Idiomas-ES%20%7C%20EN%20%7C%20PT-ED1C24)
![Versión](https://img.shields.io/badge/Versi%C3%B3n-3.1-orange)

---

##  Descripción

**David EUSA** es una aplicación de escritorio que reúne en un solo lugar:

- 🎮 Tu **biblioteca de juegos** (Steam, Epic, ejecutables locales, protocolos personalizados…).
- 🌐 Tus **apps web favoritas** (se abren en el navegador con un clic).
- 📄 Un bloc de **notas** con autoguardado.
- 👜 Un cajón de **utilidades** rápidas (calculadora, bloc de notas del sistema, log, info del sistema…).

Todo ello envuelto en una interfaz con forma de **consola portátil**: joystick, cruceta, botones A / B / X / Y y un botón gris de pantalla completa. Nada de ventanas aburridas.

---

##  Características

###  Biblioteca de juegos
- Catálogo **preinstalado con ~200 juegos** de Steam y Epic.
- Lanzamiento por **Steam URI** (`steam://run/<AppID>`), **Epic URI** (`com.epicgames.launcher://apps/...`), ejecutable local o cualquier protocolo.
- **Sincronización automática** de juegos instalados de Epic Games (lee los manifiestos `.item`).
- **Escaneo de carpetas** para detectar ejecutables `.exe` y añadirlos en bloque.
- Filtro por **categoría**, búsqueda por nombre y filtro de **favoritos**.
- Ordenación por cualquier columna.
- **Estadísticas**: partidas jugadas, último inicio y tiempo total por juego (medido automáticamente en un hilo aparte).
- **Juego aleatorio** con un solo botón.

###  Apps web
- Botones configurables con nombre + URL.
- Validación automática de URLs (añade `https://` si falta).
- Abrir todas a la vez, editar, eliminar o copiar URL con clic derecho.

###  Notas y utilidades
- Bloc de notas con **autoguardado** (debounce de 800 ms).
- Calculadora, bloc de notas del sistema, carpeta de usuario, carpeta de config, visor de log e información del sistema.

###  Personalización
- **4 temas de color**: Consola, Oscuro, Claro, Neón.
- **Color de acento personalizado** con selector de color.
- **3 idiomas**: 🇪🇸 Español · 🇬🇧 English · 🇧🇷 Português.
- **Pantalla de arranque** (Boot Screen) animada, activable y con duración ajustable.

###  Infraestructura
- Configuración guardada en `~/.david_eusa/config.json` de forma **atómica**.
- **Backups rotativos** automáticos (mantiene los últimos 5).
- **Log de errores** en `~/.david_eusa/david_eusa.log`.
- **Exportar / importar** biblioteca en JSON.
- **Exportar a CSV** para hojas de cálculo.
- Rutas verificables y editables en cualquier momento.

---

##  Captura

<img width="1874" height="947" alt="Captura de pantalla 2026-10-02 142509" src="https://github.com/user-attachments/assets/e2a30775-d3b8-4dd2-8e42-d9121b68289e" />


---

##  Instalación

### Requisitos
- **Python 3.10 o superior** (usa `list[tuple[str, str]]` y `X | None`).
- **Tkinter** (viene incluido en la instalación estándar de Python en Windows y macOS; en Linux puede requerir `sudo apt install python3-tk`).

### Pasos

```bash
# 1. Clona el repositorio
git clone https://github.com/david4524-maker/david_eusa.git
cd david_eusa

# 2. (Opcional) Crea un entorno virtual
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

# 3. Ejecuta
python david_eusa.py
```

No hay dependencias externas: **todo va con la librería estándar** de Python.

---

##  Uso

### Botones de la consola

| Botón | Acción |
|---|---|
| 🕹 **Joystick** | Enfocar el buscador de juegos |
| ⬛ **Botón gris** | Pantalla completa |
| ▲ ▼ | Moverse por la lista de juegos |
| ◀ ▶ | Cambiar de pestaña |
| 🅰 **A** | Jugar el juego seleccionado |
| 🅱 **B** | Ir a Inicio |
| ❌ **X** | Juego aleatorio |
| 💚 **Y** | Marcar / quitar favorito |

### Atajos de teclado

| Atajo | Acción |
|---|---|
| `Ctrl + 1…5` | Cambiar a pestaña (Juegos, Utilidad, Apps Web, Inicio, Notas) |
| `Ctrl + ←` / `Ctrl + →` | Pestaña anterior / siguiente |
| `Ctrl + F` | Buscar juego |
| `Ctrl + N` | Añadir juego |
| `F5` | Refrescar todo |
| `F11` | Pantalla completa |
| `Ctrl + Q` | Salir |
| `Supr` | Eliminar juego seleccionado |

---

##  Personalización

Pulsa el botón **🎨 Personalizar** de la esquina superior derecha y podrás cambiar:

- **Tema** (Consola, Oscuro, Claro, Neón).
- **Color de acento** (cualquiera, con el selector de color del sistema).
- **Idioma** (Español, English, Português).
- **Pantalla de arranque**: activar / desactivar y duración (0.5 – 10 s).

También puedes editar directamente `~/.david_eusa/config.json`:

```json
{
  "theme": "Consola",
  "accent": null,
  "language": "es",
  "boot_enabled": true,
  "boot_duracion": 2.8,
  "confirm_exit": true,
  "new_window": false,
  "notes": "",
  "webapps": [ { "name": "OSC-Browser", "url": "https://..." } ],
  "games":    [ { "name": "Minecraft", "path": "minecraft:", "category": "Sandbox" } ]
}
```

---

##  Estructura del proyecto

```
david_eusa.py         ← Todo el programa en un único archivo
~/.david_eusa/
├── config.json       ← Configuración del usuario
├── david_eusa.log    ← Log de errores
└── backups/          ← Copias rotativas de config.json
```

El código fuente está dividido en tres bloques bien separados:

1. **Constantes y catálogos** (`CATALOGO`, `CATALOGO_EPIC`, `THEMES`, `TABS`…).
2. **Utilidades** (`cargar_config`, `guardar_config`, `hacer_backup`, `abrir_con_sistema`…).
3. **Clase `App`** original y **apéndice v3.1** con Boot Screen, personalización e idiomas.

---


##  Contribuir

1. Haz un **fork** del repositorio.
2. Crea una rama: `git checkout -b mi-mejora`.
3. Haz commit: `git commit -m "Añade X"`.
4. Push: `git push origin mi-mejora`.
5. Abre un **Pull Request**.

Intenta mantener el estilo del código (type hints, nombres en español, comentarios claros).

---

##  Licencia

Este proyecto está bajo la **Licencia MIT**. Consulta el archivo [`LICENSE`](./LICENSE) para más detalles.

```
MIT License

Copyright (c) 2024 David EUSA

Por la presente se concede permiso, libre de cargos, a cualquier persona que
obtenga una copia de este software y de los archivos de documentación asociados
(el "Software"), para utilizar el Software sin restricciones, incluyendo sin
limitación los derechos a usar, copiar, modificar, fusionar, publicar,
distribuir, sublicenciar y/o vender copias del Software, y a permitir a las
personas a las que se les proporcione el Software a hacer lo mismo, sujeto a
las siguientes condiciones:

El aviso de copyright anterior y este aviso de permiso se incluirán en todas
las copias o partes sustanciales del Software.

EL SOFTWARE SE PROPORCIONA "TAL CUAL", SIN GARANTÍA DE NINGÚN TIPO, EXPRESA O
IMPLÍCITA, INCLUYENDO PERO NO LIMITADO A LAS GARANTÍAS DE COMERCIABILIDAD,
IDONEIDAD PARA UN PROPÓSITO PARTICULAR Y NO INFRACCIÓN. EN NINGÚN CASO LOS
AUTORES O TITULARES DEL COPYRIGHT SERÁN RESPONSABLES DE NINGUNA RECLAMACIÓN,
DAÑO U OTRA RESPONSABILIDAD, YA SEA EN UNA ACCIÓN DE CONTRATO, AGRAVIO O DE
OTRO MODO, QUE SURJA DE O EN CONEXIÓN CON EL SOFTWARE O EL USO U OTRO TIPO DE
ACCIONES EN EL SOFTWARE.
```

---

##  Créditos

- **Autor:** [David EUSA](https://github.com/david4524-maker)
- **Apps web integradas por defecto:**
  - [OSC-Browser](https://david4524-maker.github.io/OSC-Browser/)
  - [ezpack-ai](https://david4524-maker.github.io/ezpack-ai/)
  - [LibrePhoto](https://david4524-maker.github.io/LibrePhoto/)
- **Paleta de colores:** inspirada en el dibujo original de la consola (verde `#22B14C`, azul `#00A2E8`, celeste `#99D9EA`, morado `#A349A4`, rojo `#ED1C24`).

---

<p align="center">
  Hecho con 🎮 y mucho ☕ por David
</p>

---

## 🇬🇧 English summary

**David EUSA** is a single-file Python + Tkinter launcher that packs your games (Steam, Epic, local executables) and web apps into a retro handheld-console UI. It's cross-platform, has no third-party dependencies, ships with a boot screen, three languages (ES / EN / PT), and four themes. Licensed under MIT.

Run it with:

```bash
python david_eusa.py
```
