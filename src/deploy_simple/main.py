#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""deploy.py – Script minimalista de bootstrap (Híbrido UV/Standard)."""

import argparse
import keyword
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Validación mínima
if sys.version_info < (3, 8):
    sys.exit("❌ Requiere Python 3.8+")

LOCK_FILE = ".deploy.lock"

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


def find_python():
    """Encuentra un intérprete Python válido en el sistema."""
    # En Windows probamos 'py' primero, en Unix 'python3'
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


def run(cmd, cwd=None, env=None, silent=False, timeout=60):
    """
    Ejecuta comando con timeout.
    Si silent=True, no muestra el comando ni su salida.
    """
    if not silent:
        print(f"$ {' '.join(cmd)}")

    # Si es silencioso, redirigimos stdout y stderr a DEVNULL (oculto)
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


def clean_name(name):
    """Garantiza nombre de paquete Python válido."""
    clean = name.replace(" ", "_").replace("-", "_").lower()
    if not clean.isidentifier() or keyword.iskeyword(clean):
        sys.exit(f"❌ '{clean}' no es válido (números/reservadas).")
    return clean


# ----------------------------------------------------------------------
# LÓGICA DE NEGOCIO
# ----------------------------------------------------------------------


def create_venv(root, python_exe, version=None):
    """
    Crea venv.
    - Con uv: Soporta versiones (--python 3.12) y fix OneDrive.
    - Sin uv: Usa el python del sistema (ignora versión).
    """
    if shutil.which("uv"):
        print(f"⚙️ Creando venv con uv{' (' + version + ')' if version else ''}...")
        env = None
        if "onedrive" in str(root).lower():
            print("ℹ️ OneDrive detectado → usando copy mode")
            env = os.environ.copy()
            env["UV_LINK_MODE"] = "copy"

        cmd = [
            "uv",
            "venv",
            ".venv",
        ]
        if version:
            cmd.extend(["--python", version])
        run(cmd, cwd=root, env=env, silent=True)
    else:
        print("⚙️ Creando venv con Python estándar...")
        if version:
            print(
                f"⚠️ Aviso: Sin 'uv', la opción --python se ignora. Usando {python_exe}"
            )
        run([python_exe, "-m", "venv", ".venv"], cwd=root, silent=True)


def create_files(root, name, backend):
    """Genera estructura y archivos."""
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
        "root = true\n\n"
        "[*]\n"
        "indent_style = space\n"
        "indent_size = 4\n"
        "end_of_line = lf\n"
        "charset = utf-8\n"
        "trim_trailing_whitespace = true\n"
        "insert_final_newline = true\n\n"
        "[*.{yml,yaml}]\n"
        "indent_size = 2\n\n"
        "[Makefile]\n"
        "indent_style = tab\n",
        encoding="utf-8",
    )

    (root / ".gitignore").write_text(
        "__pycache__/\n"
        "*.py[cod]\n"
        "*$py.class\n"
        ".venv/\n"
        "venv\n"
        ".env\n"
        "dist/\n"
        "build/\n"
        "*.egg-info/\n"
        ".pytest_cache/\n"
        ".vscode/\n"
        ".idea\n"
        "*.swp\n"
        ".DS_Store\n"
        "Thumbs.db\n"
        ".deploy.lock\n",
        encoding="utf-8",
    )


def install_project(root):
    """Instala en modo editable (detecta si usar uv pip o pip normal)."""
    print("⚙️ Instalando dependencias y proyecto...")
    if shutil.which("uv"):
        run(["uv", "pip", "install", "-q", "-e", "."], cwd=root, silent=True)
        return
    # Fallback manual para encontrar el python del venv
    if platform.system() == "Windows":
        venv_python = root / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = root / ".venv" / "bin" / "python"
    if venv_python.exists():
        run(
            [str(venv_python), "-m", "pip", "install", "-q", "-e", "."],
            cwd=root,
            silent=True,
        )
    else:
        print("⚠️ No se pudo encontrar python en el venv, saltando instalación.")


def init_git(root):
    """Inicializa git de forma silenciosa."""
    if shutil.which("git"):
        print("⚙️ Inicializando Git...")
        try:
            # silent=True oculta la salida stdout/stderr
            run(["git", "init", "-b", "main"], cwd=root, silent=True)
            run(["git", "add", "."], cwd=root, silent=True)
            run(["git", "commit", "-m", "Init"], cwd=root, silent=True)
        except SystemExit:
            pass  # Ignoramos errores de git


def main():
    parser = argparse.ArgumentParser(description="Bootstrap Python (Híbrido)")
    parser.add_argument("folder", help="Nombre del proyecto")
    parser.add_argument("--backend", choices=BACKENDS.keys(), default="setuptools")
    parser.add_argument("--python", help="Versión Python (Solo con uv)", default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    name = clean_name(args.folder)
    root = Path(args.folder).resolve()
    lock = root / LOCK_FILE

    # 1. Chequeo de limpieza
    if root.exists() and any(root.iterdir()):
        if not (lock.exists() and len(list(root.iterdir())) == 1) and not args.force:
            sys.exit(f"❌ La carpeta '{root.name}' no está vacía. Usa --force.")
    if args.force and lock.exists():
        lock.unlink()
    elif lock.exists():
        sys.exit("⚠️ El proyecto ya existe.")

    # 2. Búsqueda de Python base (para el fallback)
    python_exe = find_python()
    created_by_us = not root.exists()
    try:
        print(f"🚀 Iniciando proyecto '{name}'...")
        root.mkdir(exist_ok=True)

        # 3. Creación (Usa uv si existe, o python_exe si no)
        create_venv(root, python_exe, args.python)
        # 4. Archivos
        create_files(root, name, args.backend)
        # 5. Instalación
        install_project(root)
        # 6. Git
        init_git(root)
        lock.write_text("ok")
        # Mensaje final
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
        if created_by_us and root.exists():
            shutil.rmtree(root, ignore_errors=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
