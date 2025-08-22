#!/usr/bin/env python3
"""
Setup script para SWAIF-MSG
Instala dependências e configura ambiente
"""

import subprocess
import sys
from pathlib import Path

def setup_environment():
    """Configura ambiente de desenvolvimento"""
    
    print("🚀 SWAIF-MSG Setup")
    print("="*50)
    
    # 1. Criar estrutura de pastas
    directories = [
        "depths/core",
        "depths/layers", 
        "depths/interfaces",
        "depths/tests",
        "data/backups",
        "data/logs",
        "scripts"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {dir_path}")
    
    # 2. Instalar dependências mínimas para começar
    print("\n📦 Installing core dependencies...")
    core_deps = [
        "pytest",
        "pytest-cov",
        "python-dotenv",
        "click"
    ]
    
    for dep in core_deps:
        subprocess.run([sys.executable, "-m", "pip", "install", dep])
    
    # 3. Criar arquivos __init__.py
    init_files = [
        "depths/__init__.py",
        "depths/core/__init__.py",
        "depths/layers/__init__.py",
        "depths/tests/__init__.py"
    ]
    
    for init_file in init_files:
        Path(init_file).touch()
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Run tests: pytest depths/tests/ -v")
    print("2. Test L1: python depths/run_depths.py --test")
    print("3. Monitor: python depths/run_depths.py --monitor")

if __name__ == "__main__":
    setup_environment()
