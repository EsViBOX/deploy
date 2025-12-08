# deploy.py

> **Bootstrap minimalista y robusto para proyectos Python modernos.**

Este script automatiza la creación de la estructura inicial de un proyecto Python siguiendo estándares modernos (`src-layout`, `pyproject.toml`). Está diseñado bajo la filosofía **KISS** (*Keep It Simple, Stupid*) y **EAFP** (*Easier to Ask for Forgiveness than Permission*).

## Características

*   **Prioridad `uv`**: Utiliza [uv](https://github.com/astral-sh/uv) si está instalado para una creación de entornos ultrarrápida. Hace fallback automático a `venv` estándar si no lo encuentra.
*   **Robustez en Windows/OneDrive**: Detecta automáticamente errores de *hardlinks* (comunes en OneDrive, Dropbox o entre discos) y cambia dinámicamente al modo copia sin intervención del usuario.
*   **Backends Configurables**: Soporta `setuptools` (por defecto) y `hatch`.
*   **Rollback Automático**: Si ocurre un error o cancelas la ejecución, limpia los archivos creados para no dejar basura.
*   **Seguro**: Sanitización de nombres de paquetes y validación de versiones.
*   **Zero Dependencies**: Solo utiliza la biblioteca estándar de Python.

## Requisitos

*   **Python 3.8+**
*   (Opcional) **[uv](https://docs.astral.sh/uv/)**: Recomendado para velocidad y gestión de versiones de Python.
*   (Opcional) **Git**: Para inicializar el repositorio automáticamente.

## Instalación

Simplemente descarga el archivo `deploy.py` y colócalo en una ruta accesible (o en tu carpeta de scripts personales).

```bash
# Ejemplo: Descargar con wget
wget -O deploy.py https://github.com/EsViBOX/deploy/blob/main/src/deploy_simple/main.py
```

```bash
# Ejemplo: Descargar con curl
curl -o deploy.py https://github.com/EsViBOX/deploy/blob/main/src/deploy_simple/main.py
```

## Uso

La sintaxis básica es:

```bash
python deploy.py <nombre_carpeta> [opciones]
```

### Ejemplos

**1. Básico (Backend setuptools + Python del sistema):**
```bash
python deploy.py mi_proyecto
```

**2. Moderno (Backend Hatch + Python específico con uv):**
```bash
python deploy.py mi_api --backend hatch --python 3.12
```

**3. Completo (Con Git + Forzar sobrescritura):**
```bash
python deploy.py test_app --git --force
```

### Opciones Disponibles

| Argumento | Descripción |
| :--- | :--- |
| `folder` | Nombre del proyecto/carpeta (obligatorio). Se sanitiza automáticamente (ej: `Mi Proyecto` -> `mi_proyecto`). |
| `--backend` | Elige el backend de construcción: `setuptools` (default) o `hatch`. |
| `--python` | Solicita una versión específica de Python (ej: `3.11`). **Requiere `uv` instalado**. |
| `--git` | Inicializa un repositorio Git y realiza el primer commit. |
| `--force` | Sobrescribe la carpeta si ya existe y no está vacía. |

## Estructura Generada

El script genera una estructura **src-layout** estándar:

```text
mi_proyecto/
├── src/
│   └── mi_proyecto/
│       ├── __init__.py
│       └── main.py
├── .venv/              # Entorno virtual
├── .gitignore          # Configurado para Python/uv/VSCode
├── .editorconfig       # Estilos de indentación universales
├── pyproject.toml      # Configuración del proyecto y backend
└── README.md
```

## Detalles Técnicos

### Estrategia EAFP y Hardlinks
En sistemas Windows, especialmente dentro de carpetas sincronizadas (OneDrive), la creación de *hardlinks* que utiliza `uv` para optimizar espacio suele fallar (Error 396).

Este script no intenta "adivinar" si estás en OneDrive. En su lugar:
1. Intenta la operación optimizada (hardlinks).
2. Captura la salida de error.
3. Si detecta un fallo específico de sistema de archivos/links, **reintenta automáticamente** forzando el modo copia (`UV_LINK_MODE=copy`).

### Sugerencia de Instalación Inteligente
Al finalizar, el script sugiere el comando exacto para instalar el proyecto en modo editable (`-e .`), detectando si debe añadir el flag `--link-mode=copy` basándose en el éxito o fracaso de la creación del entorno anterior.


## Licencia

MIT License

Copyright (c) 2025 EsViBOX

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.