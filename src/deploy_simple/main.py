#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
deploy.py – Bootstrap minimalista para proyectos Python.

Filosofía KISS + EAFP:
- Solo 2 backends (setuptools, hatch)
- Detección automática de herramientas (uv, git)
- EAFP: Intenta operación óptima, si falla → fallback inteligente
- Sin features innecesarias

USO:
  python deploy.py <carpeta> [--backend setuptools|hatch] [--python 3.11] [--force]

Ejemplos:
  python deploy.py mi_proyecto
  python deploy.py mi_api --backend hatch --python 3.11
  python deploy.py test --force
"""

import argparse
import keyword
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

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
    """Busca Python en PATH."""
    if platform.system() == "Windows":
        candidates = ["python", "python3"]
    else:
        candidates = ["python3", "python"]

    for cmd in candidates:
        if path := shutil.which(cmd):
            print(f"✅ Python encontrado: {path}")
            return path

    sys.exit("❌ Python no encontrado.")


def run(cmd, cwd=None, env=None):
    """Ejecuta comando. Falla si hay error."""
    print(f"ℹ️ {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, cwd=cwd, env=env)
    except subprocess.CalledProcessError as e:
        sys.exit(f"❌  Error: {e}")


def clean_name(name):
    """Sanitiza nombre de paquete Python."""
    clean = name.replace(" ", "_").replace("-", "_").lower()
    if not clean.isidentifier() or keyword.iskeyword(clean):
        sys.exit(f"❌  '{clean}' no es válido (evita números/palabras reservadas).")
    return clean


# ----------------------------------------------------------------------
# LÓGICA PRINCIPAL
# ----------------------------------------------------------------------


def create_venv(root, python_exe, version=None):
    """
    Crea venv con uv (si existe) o venv estándar.

    EAFP: Intenta operación optimizada (hardlinks). Si falla por problemas
    de filesystem (OneDrive, Dropbox, cross-drive), reintenta con copy mode.
    """
    if not shutil.which("uv"):
        print("⚙️  Creando venv con Python estándar...")
        if version:
            print("⚠️  --python requiere uv. Ignorando.")
        run([python_exe, "-m", "venv", ".venv"], cwd=root)
        return

    print(f"⚙️  Creando venv con uv{f' ({version})' if version else ''}...")

    cmd = ["uv", "venv", ".venv"]
    if version:
        cmd.extend(["--python", version])
    else:
        cmd.extend(["--python", python_exe])

    # EAFP: Intentar operación optimizada
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=root, capture_output=True, text=True)

    if result.returncode == 0:
        return True  # ✅ Éxito con hardlinks

    # Analizar el error
    error_output = (result.stderr + result.stdout).lower()

    # Errores conocidos de hardlinks:
    # - Windows: "os error 396", "os error 1314"
    # - General: "hardlink", "link mode"
    is_hardlink_error = any(
        keyword in error_output
        for keyword in ["hardlink", "link", "396", "1314", "cross-device"]
    )

    if is_hardlink_error:
        print("   ℹ️  Problema de hardlinks detectado (OneDrive/Dropbox/cross-drive)")
        print("   ℹ️  Reintentando con copy mode...")

        env = os.environ.copy()
        env["UV_LINK_MODE"] = "copy"
        run(cmd, cwd=root, env=env)
        return False
    else:
        # Otro tipo de error, mostrar y fallar
        print("\n❌  Error creando venv:")
        print(result.stderr)
        sys.exit(1)


def create_files(root, name, backend):
    """Genera estructura src-layout y archivos de configuración."""
    backend_conf = BACKENDS[backend]

    # Crear estructura de carpetas
    (root / "src" / name).mkdir(parents=True, exist_ok=True)

    # src/<name>/__init__.py
    (root / "src" / name / "__init__.py").write_text(
        '__version__ = "0.1.0"\n', encoding="utf-8"
    )

    # src/<name>/main.py
    (root / "src" / name / "main.py").write_text(
        f"def main():\n"
        f"    print('Hello from {name}!')\n"
        f"\n"
        f"if __name__ == '__main__':\n"
        f"    main()\n",
        encoding="utf-8",
    )

    # pyproject.toml
    (root / "pyproject.toml").write_text(
        f"[project]\n"
        f'name = "{name}"\n'
        f'version = "0.1.0"\n'
        f'readme = "README.md"\n'
        f'requires-python = ">=3.8"\n'
        f"dependencies = []\n"
        f"\n"
        f"[project.scripts]\n"
        f'{name} = "{name}.main:main"\n'
        f"\n"
        f"[build-system]\n"
        f"requires = {backend_conf['requires']}\n"
        f'build-backend = "{backend_conf["build-backend"]}"\n',
        encoding="utf-8",
    )

    # README.md
    (root / "README.md").write_text(
        f"# {name}\n"
        f"\n"
        f"Proyecto generado con deploy.py\n"
        f"\n"
        f"## Instalación\n"
        f"\n"
        f"```bash\n"
        f"# Activar entorno virtual\n"
        f"source .venv/bin/activate  # Linux/Mac\n"
        f".venv\\Scripts\\activate     # Windows\n"
        f"\n"
        f"# Instalar proyecto en modo desarrollo\n"
        f"pip install -e .\n"
        f"```\n",
        encoding="utf-8",
    )

    # .gitignore
    (root / ".gitignore").write_text(
        "# Python\n"
        "__pycache__/\n"
        "*.py[cod]\n"
        "*.egg-info/\n"
        "\n"
        "# Entorno virtual\n"
        ".venv/\n"
        "venv/\n"
        "\n"
        "# Build\n"
        "dist/\n"
        "build/\n"
        "\n"
        "# IDEs\n"
        ".vscode/\n"
        ".idea/\n"
        "*.swp\n"
        "\n"
        "# OS\n"
        ".DS_Store\n"
        "Thumbs.db\n"
        "\n"
        "# Deploy\n"
        ".deploy.lock\n",
        encoding="utf-8",
    )


def init_git(root):
    """Inicializa Git si está disponible. Tolerante a fallos."""
    if not shutil.which("git"):
        return

    print("⚙️  Inicializando Git...")

    try:
        run(["git", "init", "-b", "main"], cwd=root)
        run(["git", "add", "."], cwd=root)
        run(["git", "commit", "-m", "Initial commit"], cwd=root)
    except SystemExit:
        print("   ⚠️  Datos de Git incompletos o ya existe. Continuando...")


def show_next_steps(root, hardlink):
    """Muestra instrucciones finales al usuario."""
    if platform.system() == "Windows":
        activate = ".venv\\Scripts\\activate"
    else:
        activate = "source .venv/bin/activate"

    print(f"\n{'=' * 60}")
    print(f"✅ Proyecto creado: {root.name}")
    print(f"{'=' * 60}\n")
    print("Siguientes pasos:\n")
    print(f"  cd {root.name}")
    print(f"  {activate}")
    if shutil.which("uv"):
        if hardlink:
            print("  uv pip install -e .")
        else:
            print("  uv pip install -e . --link-mode=copy")
    else:
        print("  pip install -e .")
    print(f"  {root.name}\n")


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap minimalista para proyectos Python",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python deploy.py mi_proyecto
  python deploy.py mi_api --backend hatch
  python deploy.py test --python 3.11 --force
        """,
    )

    parser.add_argument("folder", help="Nombre de la carpeta del proyecto")

    parser.add_argument(
        "--backend",
        choices=BACKENDS.keys(),
        default="setuptools",
        help="Backend de construcción (default: setuptools)",
    )

    parser.add_argument(
        "--python",
        help="Versión de Python para uv (ej: 3.14.2). Requiere uv instalado.",
    )

    parser.add_argument("--git", help="Inicializar git al crear el proyecto")

    parser.add_argument(
        "--force", action="store_true", help="Sobrescribir proyecto existente"
    )

    args = parser.parse_args()

    # Preparación
    name = clean_name(args.folder)
    root = Path(args.folder).resolve()
    lock = root / LOCK_FILE

    # Validación: Carpeta limpia o --force
    if root.exists() and any(root.iterdir()):
        # Permitir si solo tiene lockfile
        if lock.exists() and len(list(root.iterdir())) == 1:
            pass
        elif not args.force:
            sys.exit(
                f"❌  La carpeta '{root.name}' no está vacía.\n"
                f"   Usa --force para sobrescribir."
            )

    if args.force and lock.exists():
        lock.unlink()
    elif lock.exists():
        sys.exit("⚠️  El proyecto ya existe. Usa --force para regenerar.")

    # Detectar Python
    python_exe = find_python()

    # Flag para rollback
    created_by_us = not root.exists()

    try:
        print(f"\n🚀 Creando proyecto '{name}' con backend '{args.backend}'...\n")

        # Flujo principal
        root.mkdir(exist_ok=True)
        hardlink = create_venv(root, python_exe, args.python)
        create_files(root, name, args.backend)

        if args.git:
            init_git(root)

        # Marcar como completado
        lock.write_text("ok")
        show_next_steps(root, hardlink)

    except KeyboardInterrupt:
        print("\n\n❌ Cancelado por el usuario.")
        if created_by_us and root.exists():
            print("🧹 Limpiando instalación incompleta...")
            try:
                shutil.rmtree(root)
            except OSError:
                print(f"⚠️  No se pudo borrar {root}. Bórralo manualmente.")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        if created_by_us and root.exists():
            print("🧹 Limpiando instalación incompleta...")
            try:
                shutil.rmtree(root)
            except OSError:
                print(f"⚠️  No se pudo borrar {root}. Bórralo manualmente.")
        sys.exit(1)


if __name__ == "__main__":
    main()
