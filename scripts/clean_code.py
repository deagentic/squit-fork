#!/usr/bin/env python3
"""
Script para limpiar código y aplicar estándares de calidad.
"""

import os
import re
import subprocess
from pathlib import Path


def remove_trailing_whitespace(file_path: Path) -> None:
    """Elimina espacios en blanco al final de las líneas."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Eliminar espacios al final de líneas
    lines = content.splitlines()
    cleaned_lines = [line.rstrip() for line in lines]
    
    # Asegurar nueva línea al final
    cleaned_content = '\n'.join(cleaned_lines) + '\n'
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)


def fix_import_order(file_path: Path) -> None:
    """Corrige el orden de imports usando isort."""
    try:
        subprocess.run(['isort', str(file_path)], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        pass  # Ignorar errores de isort


def clean_python_files(directory: Path) -> None:
    """Limpia todos los archivos Python en un directorio."""
    for file_path in directory.rglob("*.py"):
        if "__pycache__" in str(file_path):
            continue
            
        print(f"Limpiando: {file_path}")
        
        # Eliminar espacios en blanco
        remove_trailing_whitespace(file_path)
        
        # Corregir orden de imports
        fix_import_order(file_path)


def main():
    """Función principal."""
    print("🧹 Limpiando código...")
    
    # Directorio del proyecto
    project_root = Path(__file__).parent.parent
    app_dir = project_root / "app"
    
    # Limpiar archivos Python
    clean_python_files(app_dir)
    
    # Ejecutar formateo final
    print("🎨 Aplicando formateo final...")
    try:
        subprocess.run(['black', str(app_dir)], check=True, capture_output=True)
        print("✅ Formateo completado")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Error en formateo: {e}")
    
    print("🎉 Limpieza completada!")


if __name__ == "__main__":
    main()
