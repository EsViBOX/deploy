#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
deploy.py – Script minimalista de bootstrap para proyectos Python.

Este script automatiza la creación de proyectos siguiendo la filosofía KISS:
1. Detecta si 'uv' está instalado para optimizar la creación de entornos.
2. Si no, utiliza 'venv' estándar para máxima compatibilidad.
3. Genera estructura src-layout y archivos de configuración modernos.
4. Instala el proyecto en modo editable.
5. Inicializa Git (si está disponible).
"""

import argparse
import keyword
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Dict

# Validación mínima de versión de Python
if sys.version_info < (3, 8):
    sys.exit("❌ Requiere Python 3.8+")

# --- CONSTANTES GLOBALES ---
LOCK_FILE = ".deploy.lock"
TIMEOUT_SEC = 300  # 5 minutos para descargas lentas

# Detección única de herramientas al inicio (Optimización)
HAS_UV: bool = shutil.which("uv") is not None
HAS_GIT: bool = shutil.which("git") is not None

BACKENDS = {
    "setuptools": {
        "requires": '["setuptools>=61.0"]',
        "build-backend": "setuptools.build_meta",
    },
    "hatch": {
        "requires": '["hatchling"]',
        "build-backend": "hatchling.build",
    },
}

# ----------------------------------------------------------------------
# UTILIDADES
# ----------------------------------------------------------------------


def find_python() -> str:
    """
    Busca un intérprete Python válido en el sistema.

    Intenta encontrar 'py', 'python' o 'python3' en el PATH del sistema
    dependiendo del sistema operativo.

    Returns:
        str: Ruta absoluta al ejecutable de Python.

    Raises:
        SystemExit: Si no se encuentra ningún intérprete.
    """
    candidates = (
        ["python3", "python", "py"]
        if platform.system() == "Windows"
        else ["python3", "python"]
    )
    for cmd in candidates:
        path = shutil.which(cmd)
        if path:
            return path
    sys.exit("❌ Python no encontrado en el PATH.")


def run(
    cmd: List[str],
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
    silent: bool = False,
    timeout: int = TIMEOUT_SEC,
) -> None:
    """
    Ejecuta un comando del sistema de forma segura.

    Args:
        cmd: Lista de argumentos del comando (ej: ["git", "init"]).
        cwd: Directorio de trabajo opcional.
        env: Diccionario de variables de entorno opcionales.
        silent: Si es True, oculta la salida estándar y de error.
        timeout: Tiempo máximo de ejecución en segundos.

    Raises:
        SystemExit: Si el comando falla (código != 0) o expira el tiempo.
    """
    if not silent:
        print(f"$ {' '.join(cmd)}")

    std_out = subprocess.DEVNULL if silent else None

    try:
        subprocess.run(
            cmd,
            check=True,
            cwd=cwd,
            env=env,
            timeout=timeout,
            stdout=std_out,
            stderr=std_out,
        )
    except subprocess.CalledProcessError as e:
        sys.exit(f"❌ Error: {e}")
    except subprocess.TimeoutExpired:
        sys.exit("❌ Error: El comando tardó demasiado (timeout).")


def clean_name(name: str) -> str:
    """
    Sanitiza y valida el nombre del paquete Python.

    Convierte espacios y guiones a guiones bajos y verifica que sea
    un identificador válido de Python (no empieza por números, no es palabra reservada).

    Args:
        name: Nombre crudo introducido por el usuario.

    Returns:
        str: Nombre limpio y válido.

    Raises:
        SystemExit: Si el nombre es inválido.
    """
    clean = name.replace(" ", "_").replace("-", "_").lower()
    if not clean.isidentifier() or keyword.iskeyword(clean):
        sys.exit(f"❌ '{clean}' no es válido (números/reservadas).")
    return clean


# ----------------------------------------------------------------------
# LÓGICA DE NEGOCIO
# ----------------------------------------------------------------------


def create_venv(
    root: Path, python_exe: str, version: Optional[str] = None, verbose: bool = False
) -> None:
    """
    Crea el entorno virtual (.venv).

    Lógica híbrida:
    1. Si HAS_UV es True: Usa 'uv venv'. Soporta descarga de versiones de Python,
       detección de OneDrive y hardlinks.
    2. Si HAS_UV es False: Usa 'venv' estándar con el python del sistema.

    Args:
        root: Directorio raíz del proyecto.
        python_exe: Ruta al intérprete de Python del sistema (fallback).
        version: Versión específica solicitada (solo funciona con uv).
        verbose: Si es True, muestra la salida de los comandos.
    """
    is_silent = not verbose

    if HAS_UV:
        print(f"⚙️ Creando venv con uv{' (' + version + ')' if version else ''}...")
        env = None
        # Fix específico para OneDrive que no soporta hardlinks bien
        if "onedrive" in str(root).lower():
            print("ℹ️ OneDrive detectado → usando copy mode")
            env = os.environ.copy()
            env["UV_LINK_MODE"] = "copy"

        cmd = ["uv", "venv", ".venv"]
        if version:
            cmd.extend(["--python", version])

        run(cmd, cwd=root, env=env, silent=is_silent)
    else:
        print("⚙️ Creando venv con Python estándar...")
        if version:
            print(
                f"⚠️ Aviso: Sin 'uv', la opción --python se ignora. Usando {python_exe}"
            )

        run([python_exe, "-m", "venv", ".venv"], cwd=root, silent=is_silent)


def create_files(root: Path, name: str, backend: str) -> None:
    """
    Genera la estructura de carpetas y archivos de configuración.

    Crea:
    - src/<name>/__init__.py y main.py
    - pyproject.toml (configurado según el backend elegido)
    - README.md, .gitignore, .editorconfig

    Args:
        root: Directorio raíz del proyecto.
        name: Nombre sanitizado del paquete.
        backend: Backend de construcción (setuptools o hatch).
    """
    backend_conf = BACKENDS[backend]

    (root / "src" / name).mkdir(parents=True, exist_ok=True)

    (root / "README.md").write_text(
        f"# {name}\n\nGenerado con deploy.py\n", encoding="utf-8"
    )

    (root / "src" / name / "__init__.py").write_text(
        '__version__ = "0.1.0"\n', encoding="utf-8"
    )

    (root / "src" / name / "main.py").write_text(
        f"def main():\n    print('Hello from {name}!')\n\nif __name__ == '__main__':\n    main()\n",
        encoding="utf-8",
    )

    (root / "pyproject.toml").write_text(
        f'[project]\nname = "{name}"\nversion = "0.1.0"\n'
        'readme = "README.md"\n'
        f'requires-python = ">=3.8"\ndependencies = []\n\n'
        f'[project.scripts]\n{name} = "{name}.main:main"\n\n'
        f"[build-system]\nrequires = {backend_conf['requires']}\n"
        f'build-backend = "{backend_conf["build-backend"]}"\n\n'
        f"[tool.ruff]\nline-length = 88\n",
        encoding="utf-8",
    )

    (root / ".editorconfig").write_text(
        "root = true\n\n[*]\nindent_style = space\nindent_size = 4\nend_of_line = lf\n"
        "charset = utf-8\ntrim_trailing_whitespace = true\ninsert_final_newline = true\n\n"
        "[*.{yml,yaml}]\nindent_size = 2\n\n[Makefile]\nindent_style = tab\n",
        encoding="utf-8",
    )

    (root / ".gitignore").write_text(
        "__pycache__/\n*.py[cod]\n*$py.class\n.venv/\nvenv\n.env\ndist/\nbuild/\n"
        "*.egg-info/\n.pytest_cache/\n.vscode/\n.idea\n*.swp\n.DS_Store\nThumbs.db\n.deploy.lock\n",
        encoding="utf-8",
    )


def install_project(root: Path, verbose: bool = False) -> None:
    """
    Instala el proyecto en modo editable (-e .).

    Permite que los cambios en el código se reflejen inmediatamente sin reinstalar.
    Usa 'uv pip' si está disponible por rendimiento, o 'pip' estándar en su defecto.

    Args:
        root: Directorio raíz del proyecto.
        verbose: Si es True, muestra la salida de la instalación.
    """
    print("⚙️ Instalando dependencias y proyecto...")

    is_silent = not verbose
    quiet_flag = [] if verbose else ["-q"]

    if HAS_UV:
        # Usamos uv pip para velocidad
        cmd = ["uv", "pip", "install"] + quiet_flag + ["-e", "."]
        run(cmd, cwd=root, silent=is_silent)
        return

    # Fallback: Búsqueda manual del intérprete dentro del venv
    if platform.system() == "Windows":
        venv_python = root / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = root / ".venv" / "bin" / "python"

    if venv_python.exists():
        cmd = [str(venv_python), "-m", "pip", "install"] + quiet_flag + ["-e", "."]
        run(cmd, cwd=root, silent=is_silent)
    else:
        print("⚠️ No se pudo encontrar python en el venv, saltando instalación.")


def init_git(root: Path, verbose: bool = False) -> None:
    """
    Inicializa un repositorio Git local si la herramienta está disponible.

    Crea el repo, añade todos los archivos y hace el commit inicial.
    Es tolerante a fallos (ej: falta configuración de usuario).

    Args:
        root: Directorio raíz del proyecto.
        verbose: Si es True, muestra la salida de Git.
    """
    if HAS_GIT:
        print("⚙️ Inicializando Git...")
        is_silent = not verbose
        try:
            run(["git", "init", "-b", "main"], cwd=root, silent=is_silent)
            run(["git", "add", "."], cwd=root, silent=is_silent)
            run(["git", "commit", "-m", "Init"], cwd=root, silent=is_silent)
        except SystemExit:
            pass


def main() -> None:
    """Función principal de orquestación."""
    parser = argparse.ArgumentParser(description="Bootstrap Python (Híbrido)")
    parser.add_argument("folder", help="Nombre del proyecto")
    parser.add_argument("--backend", choices=BACKENDS.keys(), default="setuptools")
    parser.add_argument("--python", help="Versión Python (Solo con uv)", default=None)
    parser.add_argument("--force", action="store_true", help="Sobrescribir si existe")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Mostrar salida detallada"
    )
    args = parser.parse_args()

    name = clean_name(args.folder)
    root = Path(args.folder).resolve()
    lock = root / LOCK_FILE

    # 1. Chequeo de seguridad: Carpeta limpia
    if root.exists() and any(root.iterdir()):
        if not (lock.exists() and len(list(root.iterdir())) == 1) and not args.force:
            sys.exit(f"❌ La carpeta '{root.name}' no está vacía. Usa --force.")
    if args.force and lock.exists():
        lock.unlink()
    elif lock.exists():
        sys.exit("⚠️ El proyecto ya existe.")

    python_exe = find_python()
    created_by_us = not root.exists()

    try:
        print(f"🚀 Iniciando proyecto '{name}'...")
        root.mkdir(exist_ok=True)

        create_venv(root, python_exe, args.python, verbose=args.verbose)
        create_files(root, name, args.backend)
        install_project(root, verbose=args.verbose)
        init_git(root, verbose=args.verbose)

        lock.write_text("ok")

        sep = "\\" if platform.system() == "Windows" else "/"
        print("✅ Finalizado.\n")
        print(f"   cd {root.name}")
        print(
            f"   .venv{sep}Scripts{sep}activate"
            if platform.system() == "Windows"
            else "   source .venv/bin/activate"
        )
        print(f"   {name}")

    except Exception as e:
        print(f"❌ Fallo crítico: {e}")
        # Rollback: Limpiamos si fallamos y nosotros creamos la carpeta
        if created_by_us and root.exists():
            shutil.rmtree(root, ignore_errors=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
